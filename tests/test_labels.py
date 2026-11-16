"""Tests for fire-label rules. Skipped where the ML libraries are not installed (e.g. CI)."""
import os
import sys

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.labels import keep_flags, local_date  # noqa: E402

IST = 330  # minutes ahead of UTC


def _dates(pairs):
    d = pd.Series([p[0] for p in pairs])
    t = pd.Series([p[1] for p in pairs])
    return [str(x.date()) for x in local_date(d, t, IST)]


def test_afternoon_pass_stays_on_the_same_local_date():
    assert _dates([("2024-04-30", 714)]) == ["2024-04-30"]   # 07:14 UTC = 12:44 IST


def test_night_pass_moves_to_the_next_local_date():
    assert _dates([("2024-04-30", 2000)]) == ["2024-05-01"]  # 20:00 UTC = 01:30 IST next day


def test_boundary_at_local_midnight():
    assert _dates([("2024-04-30", 1829), ("2024-04-30", 1830)]) == ["2024-04-30", "2024-05-01"]


def test_times_before_one_am_utc_are_read_correctly():
    assert _dates([("2024-12-31", 5)]) == ["2024-12-31"]     # 00:05 UTC = 05:35 IST


def test_keep_flags_apply_all_three_filters():
    df = pd.DataFrame({
        "type": [0, 2, 0, 0, 0],
        "confidence": ["n", "n", "l", "h", "n"],
        "lc_class": [10, 10, 10, 40, 50],
    })
    out = keep_flags(df, keep_type=0, drop_confidence=["l"], exclude_lc=[40, 50])
    assert list(out["kept"]) == [True, False, False, False, False]
    assert list(out["ok_type"]) == [True, False, True, True, True]
    assert list(out["ok_conf"]) == [True, True, False, True, True]
    assert list(out["ok_lc"]) == [True, True, True, False, False]
