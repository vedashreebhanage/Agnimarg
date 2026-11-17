"""Tests for weather features, including the leakage rule. Skipped where ML libraries are missing."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("xarray")
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.features_weather import HISTORY, daily_from_hourly, history_features, hourly_rain_mm  # noqa: E402


def _daily(n_days=120, seed=0):
    rng = np.random.default_rng(seed)
    shape = (n_days, 2, 3)
    return {"precip_mm": rng.gamma(0.3, 8.0, shape), "tmax_c": rng.normal(25, 5, shape),
            "vpd_max_kpa": rng.uniform(0.2, 4.0, shape)}


# ---- leakage: history features for day D must not depend on day D or any later day ----

@pytest.mark.parametrize("day", [95, 100, 119])
def test_history_features_ignore_the_prediction_day_and_the_future(day):
    base = _daily()
    changed = {k: v.copy() for k, v in base.items()}
    for v in changed.values():
        v[day:] += 1000.0                      # alter day D and everything after it
    a, b = history_features(base), history_features(changed)
    for name in HISTORY:
        assert np.array_equal(a[name][: day + 1], b[name][: day + 1], equal_nan=True), name


def test_history_features_do_respond_to_the_day_before():
    base = _daily()
    changed = {k: v.copy() for k, v in base.items()}
    changed["precip_mm"][99] += 50.0
    a, b = history_features(base), history_features(changed)
    assert not np.array_equal(a["rain_7d_mm"][100], b["rain_7d_mm"][100])
    assert np.array_equal(a["rain_7d_mm"][99], b["rain_7d_mm"][99])


def test_rain_sums_match_a_direct_calculation():
    d = _daily()
    h = history_features(d)
    assert np.allclose(h["rain_7d_mm"][50], d["precip_mm"][43:50].sum(axis=0))
    assert np.allclose(h["rain_90d_mm"][100], d["precip_mm"][10:100].sum(axis=0))
    assert np.isnan(h["rain_30d_mm"][29]).all() and not np.isnan(h["rain_30d_mm"][30]).any()


def test_days_since_rain_counts_from_the_last_wet_day():
    d = _daily(10)
    d["precip_mm"][:] = 0.0
    d["precip_mm"][3] = 5.0
    since = history_features(d)["days_since_rain"]
    assert np.isnan(since[3]).all()            # no rain day seen before day 3
    assert (since[4] == 0).all() and (since[7] == 3).all()


# ---- rainfall running totals to hourly amounts ----

def test_running_totals_become_hourly_amounts():
    # Hours 23, 00, 01, 02 UTC. Totals: 4 mm by 23:00, 6 mm by 00:00 (day total), then a new day.
    tp = np.array([0.004, 0.006, 0.001, 0.003]).reshape(4, 1, 1)
    rain = hourly_rain_mm(tp, np.array([23, 0, 1, 2]), prev_tp_m=np.array([[0.003]]))
    assert np.allclose(rain.ravel(), [1.0, 2.0, 1.0, 2.0])


def test_first_hour_without_a_previous_total_is_unknown():
    tp = np.array([0.006, 0.001]).reshape(2, 1, 1)
    rain = hourly_rain_mm(tp, np.array([0, 1]), prev_tp_m=None)
    assert np.isnan(rain[0, 0, 0]) and rain[1, 0, 0] == pytest.approx(1.0)


# ---- hourly to daily ----

def test_daily_values_from_one_known_day():
    t = np.linspace(10, 33, 24).reshape(24, 1, 1)
    td = np.full((24, 1, 1), 10.0)
    dates, d = daily_from_hourly(np.repeat(np.datetime64("2024-04-30"), 24), t, td,
                                 np.full((24, 1, 1), 2.0), np.full((24, 1, 1), 0.5), np.full((24, 1, 1), 0.3))
    assert len(dates) == 1
    assert d["tmax_c"][0, 0, 0] == pytest.approx(33.0) and d["tmin_c"][0, 0, 0] == pytest.approx(10.0)
    assert d["precip_mm"][0, 0, 0] == pytest.approx(12.0)
    assert d["rh_min_pct"][0, 0, 0] < 30 and d["vpd_max_kpa"][0, 0, 0] > 3.5   # hot afternoon, dry air


def test_incomplete_days_are_rejected():
    a = np.zeros((23, 1, 1))
    with pytest.raises(ValueError):
        daily_from_hourly(np.repeat(np.datetime64("2024-04-30"), 23), a, a, a, a, a)
