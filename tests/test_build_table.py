"""Tests for the training-table rules, including fire-history leakage. Skipped without ML libraries."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.build_table import assign_split, keep_mask, recent_and_so_far, season_of  # noqa: E402

SPLITS = {"train_last_season": 2022, "valid_seasons": [2023], "test_first_season": 2024}


def test_season_is_named_by_the_year_it_ends():
    s = season_of(pd.to_datetime(["2023-11-01", "2023-12-31", "2024-01-01", "2024-06-30"]), end_month=6)
    assert list(s) == [2024, 2024, 2024, 2024]


def test_splits_follow_the_seasons():
    assert list(assign_split(np.array([2019, 2022, 2023, 2024, 2026]), SPLITS)) == ["train", "train", "valid", "test", "test"]


def test_fire_rows_are_always_kept_and_sampling_is_repeatable():
    rng = np.random.default_rng(1)
    cell, day = rng.integers(0, 100_000, 200_000), rng.integers(17_000, 20_000, 200_000)
    fire = rng.random(200_000) < 0.01
    a = keep_mask(cell, day, fire, 0.05, seed=7)
    assert a[fire].all()
    assert 0.045 < a[~fire].mean() < 0.055
    order = rng.permutation(len(cell))      # same rows in a different order give the same choices
    assert np.array_equal(keep_mask(cell[order], day[order], fire[order], 0.05, seed=7), a[order])
    assert not np.array_equal(keep_mask(cell, day, fire, 0.05, seed=8), a)


def _fires(days=40, nrow=6, ncol=6, seed=0):
    return (np.random.default_rng(seed).random((days, nrow * ncol)) < 0.05).astype(np.int8)


@pytest.mark.parametrize("day", [10, 20, 39])
def test_fire_history_ignores_the_prediction_day_and_the_future(day):
    F = _fires()
    G = F.copy()
    G[day:] = 1 - G[day:]                    # change every fire from day D onwards
    r1, s1 = recent_and_so_far(F, 6, 6, radius=1, recent_days=7, season_start=7)
    r2, s2 = recent_and_so_far(G, 6, 6, radius=1, recent_days=7, season_start=7)
    assert np.array_equal(r1[: day + 1], r2[: day + 1]) and np.array_equal(s1[: day + 1], s2[: day + 1])


def test_fire_history_counts_known_fires():
    F = np.zeros((12, 9), dtype=np.int8)     # 3 x 3 grid
    F[8, 4] = 1                              # centre cell burns on day 8
    recent, so_far = recent_and_so_far(F, 3, 3, radius=1, recent_days=3, season_start=5)
    assert recent[8, 0] == 0                 # not yet: day 8 itself is excluded
    assert (recent[9] == 1).all() and (recent[11] == 1).all()   # every cell is a neighbour of the centre
    assert recent[12 - 1, 4] == 1 and so_far[9, 4] == 1 and so_far[9, 0] == 0
    assert so_far[8, 4] == 0


def test_fires_before_the_season_do_not_count_as_so_far():
    F = np.zeros((10, 1), dtype=np.int8)
    F[2, 0] = 1                              # in the lead-in period
    _, so_far = recent_and_so_far(F, 1, 1, radius=0, recent_days=7, season_start=5)
    assert (so_far == 0).all()
