"""Daily weather features from hourly ERA5-Land, per weather cell (about 9 km) and local date.

Same-day features describe the weather on the prediction date itself. In training they come from
ERA5-Land; in live use they must come from a weather forecast for that date:
  tmax_c, tmin_c, rh_min_pct, vpd_max_kpa, wind_max_ms, wind_mean_ms, precip_mm, soil_moist

History features use only days BEFORE the prediction date:
  rain_7d_mm, rain_30d_mm, rain_90d_mm, days_since_rain, tmax_7d_c, vpd_7d_kpa

Outputs: weather_daily/<year>.parquet (one row per weather cell per date) and
weather_cell_map.parquet (which weather cell each 1 km grid cell uses: the nearest one).

ERA5-Land rainfall is a running total since 00:00 UTC that restarts each day; it is converted to
hourly amounts first. Days are local (IST) days, to match the fire labels.

Usage:  python -m ml.features_weather config/uttarakhand.yaml
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import xarray as xr

from imagery.grid import load_config

SAME_DAY = ["tmax_c", "tmin_c", "rh_min_pct", "vpd_max_kpa", "wind_max_ms", "wind_mean_ms", "precip_mm", "soil_moist"]
HISTORY = ["rain_7d_mm", "rain_30d_mm", "rain_90d_mm", "days_since_rain", "tmax_7d_c", "vpd_7d_kpa"]
RAIN_DAY_MM = 1.0
HOUR = np.timedelta64(1, "h")


def saturation_vapour_pressure_kpa(temp_c: np.ndarray) -> np.ndarray:
    """Magnus formula: the most water vapour air can hold at this temperature, as a pressure."""
    return 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3))


def hourly_rain_mm(tp_m: np.ndarray, hour_utc: np.ndarray, prev_tp_m: np.ndarray | None) -> np.ndarray:
    """Convert ERA5-Land running totals (metres since 00 UTC) to millimetres per hour.

    The value stamped 01:00 is the first hour of a new day's total; every other hour is the
    difference from the hour before. `prev_tp_m` is the total at the hour before the first row
    (None if unknown, in which case the first row is NaN unless it is stamped 01:00).
    """
    prev = np.concatenate([(np.full_like(tp_m[:1], np.nan) if prev_tp_m is None else prev_tp_m[None]), tp_m[:-1]])
    rain = np.where((hour_utc == 1)[:, None, None], tp_m, tp_m - prev) * 1000.0
    return np.maximum(rain, 0.0, out=rain, where=~np.isnan(rain))


def daily_from_hourly(local_date: np.ndarray, t_c, td_c, wind, rain_mm, soil) -> tuple[np.ndarray, dict]:
    """Aggregate hourly arrays (time, lat, lon) to daily. Every date must have exactly 24 hours."""
    dates, counts = np.unique(local_date, return_counts=True)
    if not (counts == 24).all():
        raise ValueError("daily_from_hourly needs complete days of 24 hours")
    n = len(dates)
    shp = (n, 24) + t_c.shape[1:]
    t, td, w, r, s = (a.reshape(shp) for a in (t_c, td_c, wind, rain_mm, soil))
    es, ea = saturation_vapour_pressure_kpa(t), saturation_vapour_pressure_kpa(td)
    return dates, {
        "tmax_c": t.max(axis=1), "tmin_c": t.min(axis=1),
        "rh_min_pct": np.clip(100.0 * ea / es, 0, 100).min(axis=1),
        "vpd_max_kpa": np.maximum(es - ea, 0).max(axis=1),
        "wind_max_ms": w.max(axis=1), "wind_mean_ms": w.mean(axis=1),
        "precip_mm": r.sum(axis=1), "soil_moist": s.mean(axis=1),
    }


def history_features(daily: dict) -> dict:
    """Features for day D built only from days before D. Arrays are (day, lat, lon)."""
    rain, tmax, vpd = daily["precip_mm"], daily["tmax_c"], daily["vpd_max_kpa"]

    def prior_sum(a: np.ndarray, k: int) -> np.ndarray:
        c = np.concatenate([np.zeros_like(a[:1]), np.cumsum(a, axis=0)])      # c[i] = sum of days 0..i-1
        out = np.full(a.shape, np.nan, dtype=np.float64)
        out[k:] = c[k:-1] - c[:-k - 1]                                         # days D-k .. D-1
        return out

    since = np.full(rain.shape, np.nan)
    run = np.full(rain.shape[1:], np.nan)          # unknown until the first rain day is seen
    for d in range(rain.shape[0]):
        since[d] = run                              # value as of the end of day D-1
        run = np.where(rain[d] >= RAIN_DAY_MM, 0.0, run + 1.0)
    return {
        "rain_7d_mm": prior_sum(rain, 7), "rain_30d_mm": prior_sum(rain, 30), "rain_90d_mm": prior_sum(rain, 90),
        "days_since_rain": since,
        "tmax_7d_c": prior_sum(tmax, 7) / 7.0, "vpd_7d_kpa": prior_sum(vpd, 7) / 7.0,
    }


def load_daily(files: list[str], utc_offset_minutes: int):
    """Read monthly hourly files in order and return (dates, daily dict, latitudes, longitudes)."""
    offset = np.timedelta64(utc_offset_minutes, "m")
    buf = None            # hourly rows not yet part of a complete local day
    prev_tp, last_time = None, None
    all_dates, parts, lat, lon = [], {k: [] for k in SAME_DAY}, None, None
    for path in files:
        with xr.open_dataset(path) as ds:
            times = ds["valid_time"].values.astype("datetime64[h]")
            if lat is None:
                lat, lon = ds["latitude"].values, ds["longitude"].values
            elif not (np.array_equal(lat, ds["latitude"].values) and np.array_equal(lon, ds["longitude"].values)):
                raise ValueError(f"{path}: grid differs from earlier files")
            if (np.diff(times) != HOUR).any() or (last_time is not None and times[0] - last_time != HOUR):
                raise ValueError(f"{path}: hours are missing or out of order")
            tp = ds["tp"].values
            cur = {
                "t": ds["t2m"].values - 273.15, "td": ds["d2m"].values - 273.15,
                "w": np.hypot(ds["u10"].values, ds["v10"].values),
                "r": hourly_rain_mm(tp, (times - times.astype("datetime64[D]")).astype(int), prev_tp),
                "s": ds["swvl1"].values,
            }
        prev_tp, last_time = tp[-1], times[-1]
        # An hourly rain amount covers the hour ending at its time stamp, so every variable is
        # assigned to the local date of that hour's start.
        ldate = (times - HOUR + offset).astype("datetime64[D]")
        if buf is not None:
            ldate = np.concatenate([buf["d"], ldate])
            cur = {k: np.concatenate([buf[k], v]) for k, v in cur.items()}
        dates, counts = np.unique(ldate, return_counts=True)
        done = dates[counts == 24]
        # A partial local day at the very start of the record is dropped; a partial day at the
        # end of this file is held back and completed by the next file.
        keep = np.isin(ldate, done)
        tail = ldate > (done[-1] if len(done) else ldate[0] - 1)
        if keep.any():
            d, daily = daily_from_hourly(ldate[keep], cur["t"][keep], cur["td"][keep], cur["w"][keep], cur["r"][keep], cur["s"][keep])
            all_dates.append(d)
            for k in SAME_DAY:
                parts[k].append(daily[k].astype(np.float32))
        buf = {"d": ldate[tail], **{k: v[tail] for k, v in cur.items()}}
    dates = np.concatenate(all_dates)
    if (np.diff(dates) != np.timedelta64(1, "D")).any():
        raise ValueError("daily record has gaps")
    return dates, {k: np.concatenate(v) for k, v in parts.items()}, lat, lon


def build(cfg: dict, out_dir: str | None = None) -> pd.DataFrame:
    out_dir = out_dir or cfg["output_dir"]
    w = cfg["weather"]
    files = sorted(glob.glob(os.path.join(w["source_dir"], "era5land_*.nc")))
    if not files:
        raise FileNotFoundError("no ERA5-Land files found")
    dates, daily, lat, lon = load_daily(files, cfg["labels"]["utc_offset_minutes"])
    feats = {**daily, **{k: v.astype(np.float32) for k, v in history_features(daily).items()}}

    nlat, nlon = len(lat), len(lon)
    wcell = np.arange(nlat * nlon, dtype=np.int16)
    os.makedirs(os.path.join(out_dir, "weather_daily"), exist_ok=True)
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    for y in np.unique(years):
        m = years == y
        nd = int(m.sum())
        df = pd.DataFrame({"wcell": np.tile(wcell, nd), "date": np.repeat(dates[m].astype("datetime64[ns]"), nlat * nlon)})
        for k in SAME_DAY + HISTORY:
            df[k] = feats[k][m].reshape(nd * nlat * nlon)
        df.to_parquet(os.path.join(out_dir, "weather_daily", f"{y}.parquet"), index=False)

    # Nearest weather cell for each 1 km grid cell.
    grid = pd.read_parquet(os.path.join(cfg["output_dir"], "grid.parquet"), columns=["cell_id", "lon", "lat"])
    ilat = np.abs(grid["lat"].to_numpy()[:, None] - lat[None, :]).argmin(axis=1)
    ilon = np.abs(grid["lon"].to_numpy()[:, None] - lon[None, :]).argmin(axis=1)
    cmap = pd.DataFrame({"cell_id": grid["cell_id"], "wcell": (ilat * nlon + ilon).astype(np.int16)})
    cmap.to_parquet(os.path.join(out_dir, "weather_cell_map.parquet"), index=False)

    summary = pd.DataFrame({k: [np.nanmin(v), np.nanmean(v), np.nanmax(v), float(np.isnan(v).mean())] for k, v in feats.items()},
                           index=["min", "mean", "max", "share_missing"]).T
    summary.attrs.update(first=str(dates[0]), last=str(dates[-1]), days=len(dates), files=len(files),
                         weather_cells_used=int(cmap["wcell"].nunique()))
    return summary


if __name__ == "__main__":
    cfg = load_config(sys.argv[1])
    s = build(cfg, sys.argv[2] if len(sys.argv) > 2 else None)
    print({k: v for k, v in s.attrs.items()})
    print(s.round(2).to_string())
