"""Build the training table: one row per forest cell per day of the fire season, with its label,
all features, its split (train / valid / test) and a sampling weight.

A fire season runs from November to June and is named by the year it ends (Nov 2023 - Jun 2024 is
season 2024). All fire cell-days are kept. No-fire cell-days are sampled, because fire is rare and
the full table would not fit in memory; each kept no-fire row carries weight 1 / sampling rate so
totals and probabilities can be corrected back to the real proportions.

Fire-history features use only fires from BEFORE the prediction date:
  fire_days_last_season    fire days in this cell in the previous season
  fire_rate_prior_seasons  average fire days per earlier season in this cell
  fire_days_season_so_far  fire days in this cell earlier in the current season
  nbr_fire_recent          fire cell-days within the neighbourhood over the previous N days

Output: table/<season>.parquet in the region's output folder.

Usage:  python -m ml.build_table config/uttarakhand.yaml
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.ndimage import convolve

from imagery.grid import load_config
from ml.features_weather import HISTORY, SAME_DAY

MASK64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def season_of(dates: pd.Series | pd.DatetimeIndex, end_month: int) -> np.ndarray:
    d = pd.DatetimeIndex(dates)
    return np.where(d.month > end_month, d.year + 1, d.year).astype(np.int16)


def assign_split(season: np.ndarray, splits: dict) -> np.ndarray:
    out = np.full(season.shape, "", dtype=object)
    out[season <= splits["train_last_season"]] = "train"
    out[np.isin(season, splits["valid_seasons"])] = "valid"
    out[season >= splits["test_first_season"]] = "test"
    if (out == "").any():
        raise ValueError("some seasons are not assigned to a split")
    return out


def _splitmix64(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.uint64)
    with np.errstate(over="ignore"):
        x = (x + np.uint64(0x9E3779B97F4A7C15)) & MASK64
        x = ((x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)) & MASK64
        x = ((x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)) & MASK64
        return x ^ (x >> np.uint64(31))


def keep_mask(cell_id: np.ndarray, day_number: np.ndarray, is_fire: np.ndarray, rate: float, seed: int) -> np.ndarray:
    """Which rows to keep. Fire rows always; no-fire rows with probability `rate`.

    The choice for a row depends only on (cell, day, seed), never on processing order, so the
    table is identical however it is built.
    """
    key = (cell_id.astype(np.uint64) << np.uint64(20)) ^ day_number.astype(np.uint64) ^ np.uint64(seed)
    u = (_splitmix64(key) >> np.uint64(11)).astype(np.float64) / float(1 << 53)
    return is_fire | (u < rate)


def recent_and_so_far(F: np.ndarray, nrow: int, ncol: int, radius: int, recent_days: int, season_start: int):
    """F: (days, cells) 0/1 fire array in date order. Returns two (days, cells) arrays where the
    value for day d uses only days before d:
      so_far[d] = fires in the same cell on days season_start..d-1 (0 before season_start)
      recent[d] = fires within the (2*radius+1)^2 neighbourhood on days d-recent_days..d-1
    """
    days = F.shape[0]
    k = np.ones((1, 2 * radius + 1, 2 * radius + 1), dtype=np.int32)
    box = convolve(F.reshape(days, nrow, ncol).astype(np.int32), k, mode="constant").reshape(days, -1)
    cb = np.concatenate([np.zeros((1, box.shape[1]), np.int64), np.cumsum(box, axis=0)])
    idx = np.arange(days)
    lo = np.maximum(idx - recent_days, 0)
    recent = cb[idx] - cb[lo]
    cf = np.concatenate([np.zeros((1, F.shape[1]), np.int64), np.cumsum(F, axis=0)])
    so_far = cf[idx] - cf[season_start]
    so_far[idx < season_start] = 0
    return recent.astype(np.int16), so_far.astype(np.int16)


def build(cfg: dict, out_dir: str | None = None) -> pd.DataFrame:
    base = cfg["output_dir"]
    out_dir = out_dir or base
    tb, lab = cfg["table"], cfg["labels"]
    with open(os.path.join(base, "grid_meta.yaml"), encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    nrow, ncol = meta["nrow"], meta["ncol"]

    grid = pd.read_parquet(os.path.join(base, "grid.parquet"))
    cells = grid[grid["is_forest"]]
    static = (cells[["cell_id", "lat", "lon", "frac_tree", "frac_shrub", "frac_grass", "frac_crop", "frac_built"]]
              .merge(pd.read_parquet(os.path.join(base, "terrain.parquet")).drop(columns="dem_pixels"), on="cell_id")
              .merge(pd.read_parquet(os.path.join(base, "static.parquet")), on="cell_id")
              .merge(pd.read_parquet(os.path.join(out_dir, "weather_cell_map.parquet")), on="cell_id"))
    if len(static) != len(cells):
        raise ValueError("a feature file is missing forest cells")
    cell_ids = static["cell_id"].to_numpy()

    wdir = os.path.join(out_dir, "weather_daily")
    weather = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(wdir, "*.parquet")))], ignore_index=True)
    w_last = weather["date"].max()

    fires = pd.read_parquet(os.path.join(base, "fire_cell_days.parquet"))
    fires = fires[fires["fire"]][["cell_id", "date"]]
    start = pd.Timestamp(lab["label_start_date"])
    fires = fires[(fires["date"] >= start) & (fires["date"] <= w_last)]
    fires["season"] = season_of(fires["date"], tb["season_end_month"])
    per_season = fires.groupby(["cell_id", "season"]).size().rename("n").reset_index()

    months = set(tb["season_months"])
    all_days = pd.date_range(start, w_last, freq="D")
    season_days = all_days[all_days.month.isin(months)]
    seasons = np.unique(season_of(season_days, tb["season_end_month"]))
    first_season = int(season_of(pd.DatetimeIndex([start]), tb["season_end_month"])[0])

    os.makedirs(os.path.join(out_dir, "table"), exist_ok=True)
    summary = []
    for s in seasons:
        sdays = season_days[season_of(season_days, tb["season_end_month"]) == s]
        lead = pd.date_range(sdays[0] - pd.Timedelta(days=tb["recent_fire_days"]), sdays[0] - pd.Timedelta(days=1))
        days = lead.append(sdays)
        # dense fire array over all grid cells (neighbours can be non-forest)
        F = np.zeros((len(days), nrow * ncol), dtype=np.int8)
        fs = fires[fires["date"].isin(days)]
        F[days.get_indexer(fs["date"]), fs["cell_id"].to_numpy()] = 1
        recent, so_far = recent_and_so_far(F, nrow, ncol, tb["neighbour_radius_cells"], tb["recent_fire_days"], len(lead))
        recent, so_far, Fs = recent[len(lead):][:, cell_ids], so_far[len(lead):][:, cell_ids], F[len(lead):][:, cell_ids]

        nd, nc = len(sdays), len(cell_ids)
        cid = np.tile(cell_ids, nd)
        dnum = np.repeat((sdays.values.astype("datetime64[D]").astype(np.int64)), nc)
        is_fire = Fs.ravel().astype(bool)
        split = assign_split(np.array([s]), tb["splits"])[0]
        rate = tb["sample_rate_train"] if split == "train" else tb["sample_rate_eval"]
        keep = keep_mask(cid, dnum, is_fire, rate, cfg["seed"])

        df = pd.DataFrame({
            "season": np.int16(s), "split": split,
            "date": pd.to_datetime(dnum[keep], unit="D"), "cell_id": cid[keep].astype(np.int32),
            "fire": is_fire[keep].astype(np.int8),
            "weight": np.where(is_fire[keep], 1.0, 1.0 / rate).astype(np.float32),
            "fire_days_season_so_far": so_far.ravel()[keep], "nbr_fire_recent": recent.ravel()[keep],
        })
        prev = per_season[per_season["season"] == s - 1].set_index("cell_id")["n"]
        prior = per_season[per_season["season"] < s].groupby("cell_id")["n"].sum()
        n_prior = s - first_season
        df["fire_days_last_season"] = (df["cell_id"].map(prev).fillna(0).astype(np.float32)
                                       if s - 1 >= first_season else np.float32(np.nan))
        df["fire_rate_prior_seasons"] = ((df["cell_id"].map(prior).fillna(0) / n_prior).astype(np.float32)
                                         if n_prior > 0 else np.float32(np.nan))
        df["doy"] = df["date"].dt.dayofyear.astype(np.int16)
        df = df.merge(static, on="cell_id", how="left")
        df = df.merge(weather[["wcell", "date"] + SAME_DAY + HISTORY], on=["wcell", "date"], how="left")
        if df[SAME_DAY].isna().any(axis=None):
            raise ValueError(f"season {s}: some rows have no weather")
        df.to_parquet(os.path.join(out_dir, "table", f"{s}.parquet"), index=False)
        summary.append({"season": int(s), "split": split, "first": str(sdays[0].date()), "last": str(sdays[-1].date()),
                        "rows": len(df), "fire_rows": int(df["fire"].sum()),
                        "fire_share_real": float(is_fire.mean()), "fire_share_weighted": float(np.average(df["fire"], weights=df["weight"]))})
    return pd.DataFrame(summary)


if __name__ == "__main__":
    cfg = load_config(sys.argv[1])
    s = build(cfg, sys.argv[2] if len(sys.argv) > 2 else None)
    print(s.to_string(index=False))
