"""Turn FIRMS satellite fire detections into fire labels on the 1 km grid.

Outputs (in the region's output folder):
  detections.parquet     every detection inside the region, with its grid cell, local date, the
                         land-cover class under its centre, and whether it is kept for labelling
  fire_cell_days.parquet one row per (cell, local date) that has at least one kept detection

A detection is kept when it is a presumed vegetation fire (FIRMS type), is not low confidence, and
its centre does not fall on cropland or built-up land. A cell-day is a fire if any of the label
satellites has a kept detection. Cell-days before the label start date are left out, because not
all label satellites were operating then.

Known limit: these are satellite detections, so small fires and fires under cloud are missed.

Usage:  python -m ml.labels config/uttarakhand.yaml
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import rasterio
import yaml
from pyproj import Transformer
from rasterio.windows import Window

from imagery.grid import cell_index, load_config, region_polygon

LC_BLOCK = 1024  # land-cover pixels per side read at a time


def local_date(acq_date: pd.Series, acq_time: pd.Series, utc_offset_minutes: int) -> pd.Series:
    """FIRMS gives date and HHMM time in UTC. Return the calendar date in local time."""
    hhmm = acq_time.astype(int)
    utc = pd.to_datetime(acq_date) + pd.to_timedelta(hhmm // 100, unit="h") + pd.to_timedelta(hhmm % 100, unit="m")
    return (utc + pd.Timedelta(minutes=utc_offset_minutes)).dt.normalize()


def keep_flags(df: pd.DataFrame, keep_type: int, drop_confidence: list[str], exclude_lc: list[int]) -> pd.DataFrame:
    """Add one boolean column per filter, and `kept` = passes all of them."""
    out = df.copy()
    out["ok_type"] = out["type"] == keep_type
    out["ok_conf"] = ~out["confidence"].astype(str).isin(drop_confidence)
    out["ok_lc"] = ~out["lc_class"].isin(exclude_lc)
    out["kept"] = out["ok_type"] & out["ok_conf"] & out["ok_lc"]
    return out


def read_detections(path: str, sensor: str, bounds: tuple[float, float, float, float]) -> pd.DataFrame:
    """Read one FIRMS CSV in chunks, keeping only rows inside the bounding box."""
    west, south, east, north = bounds
    cols = ["latitude", "longitude", "acq_date", "acq_time", "confidence", "frp", "daynight", "type"]
    parts = []
    for ch in pd.read_csv(path, usecols=cols, dtype={"confidence": "string", "acq_time": "int32"}, chunksize=500_000):
        m = ch["latitude"].between(south, north) & ch["longitude"].between(west, east)
        parts.append(ch[m])
    df = pd.concat(parts, ignore_index=True)
    df["sensor"] = sensor
    return df


def sample_land_cover(lon: np.ndarray, lat: np.ndarray, tile_dir: str) -> np.ndarray:
    """WorldCover class under each point (0 where no tile covers it). Reads block by block."""
    out = np.zeros(len(lon), dtype=np.uint8)
    for tile in sorted(glob.glob(os.path.join(tile_dir, "*_Map.tif"))):
        with rasterio.open(tile) as src:
            b = src.bounds
            sel = np.flatnonzero((lon >= b.left) & (lon < b.right) & (lat > b.bottom) & (lat <= b.top))
            if len(sel) == 0:
                continue
            col = np.floor((lon[sel] - src.transform.c) / src.transform.a).astype(np.int64).clip(0, src.width - 1)
            row = np.floor((lat[sel] - src.transform.f) / src.transform.e).astype(np.int64).clip(0, src.height - 1)
            block = (row // LC_BLOCK) * 100_000 + (col // LC_BLOCK)
            order = np.argsort(block, kind="stable")
            starts = np.flatnonzero(np.r_[True, np.diff(block[order]) != 0])
            ends = np.r_[starts[1:], len(order)]
            for s, e in zip(starts, ends):
                idx = order[s:e]
                r0, c0 = (row[idx[0]] // LC_BLOCK) * LC_BLOCK, (col[idx[0]] // LC_BLOCK) * LC_BLOCK
                h, w = min(LC_BLOCK, src.height - r0), min(LC_BLOCK, src.width - c0)
                data = src.read(1, window=Window(c0, r0, w, h))
                out[sel[idx]] = data[row[idx] - r0, col[idx] - c0]
    return out


def build(cfg: dict, out_dir: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    out_dir = out_dir or cfg["output_dir"]
    grid = pd.read_parquet(os.path.join(cfg["output_dir"], "grid.parquet"))
    with open(os.path.join(cfg["output_dir"], "grid_meta.yaml"), encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    lab = cfg["labels"]

    bounds = tuple(region_polygon(cfg).total_bounds)
    det = pd.concat([read_detections(p, s, bounds) for s, p in lab["sources"].items()], ignore_index=True)

    # Grid cell of each detection; drop detections outside the region.
    x, y = Transformer.from_crs(4326, meta["crs"], always_xy=True).transform(det["longitude"].to_numpy(), det["latitude"].to_numpy())
    row, col, ok = cell_index(x, y, meta["x0"], meta["y0"], meta["cell_size_m"], meta["ncol"], meta["nrow"])
    det["cell_id"] = (row * meta["ncol"] + col).astype(np.int64)
    det = det[ok & det["cell_id"].isin(grid["cell_id"])].reset_index(drop=True)
    det["cell_id"] = det["cell_id"].astype(np.int32)

    det["date"] = local_date(det["acq_date"], det["acq_time"], lab["utc_offset_minutes"])
    det["lc_class"] = sample_land_cover(det["longitude"].to_numpy(), det["latitude"].to_numpy(), cfg["land_cover"]["source_dir"])
    det = keep_flags(det, lab["keep_type"], lab["drop_confidence"], lab["exclude_land_cover"])
    det = det.merge(grid[["cell_id", "is_forest"]], on="cell_id", how="left")

    kept = det[det["kept"]]
    kept = kept[kept["date"] >= pd.Timestamp(lab["label_start_date"])]
    counts = kept.groupby(["cell_id", "date", "sensor"]).size().unstack("sensor", fill_value=0)
    counts.columns = [f"n_{c}" for c in counts.columns]
    days = counts.join(kept.groupby(["cell_id", "date"])["frp"].max().rename("frp_max")).reset_index()
    days["fire"] = days[[f"n_{s}" for s in lab["label_sensors"]]].sum(axis=1) > 0
    days = days.merge(grid[["cell_id", "is_forest"]], on="cell_id", how="left")

    os.makedirs(out_dir, exist_ok=True)
    det.drop(columns=["acq_date"]).to_parquet(os.path.join(out_dir, "detections.parquet"), index=False)
    days.to_parquet(os.path.join(out_dir, "fire_cell_days.parquet"), index=False)
    return det, days


def report(det: pd.DataFrame, days: pd.DataFrame, cfg: dict) -> None:
    sensors = cfg["labels"]["label_sensors"]
    print(f"detections inside region: {len(det)}")
    print(det.groupby("sensor").agg(n=("kept", "size"), first=("date", "min"), last=("date", "max")).to_string())
    for c in ("ok_type", "ok_conf", "ok_lc", "kept"):
        print(f"  pass {c}: {det[c].mean():.1%}")
    k = det[det["kept"] & det["sensor"].isin(sensors)]
    print(f"kept detections ({'+'.join(sensors)}): {len(k)}; in forest cells: {k['is_forest'].mean():.1%}")
    print("land cover under kept detections (class: share): " +
          ", ".join(f"{c}: {s:.1%}" for c, s in k["lc_class"].value_counts(normalize=True).head(6).items()))
    f = days[days["fire"]]
    print(f"fire cell-days from {cfg['labels']['label_start_date']}: {len(f)}; in forest cells: {int(f['is_forest'].sum())}")
    print("fire cell-days in forest cells per year: " +
          ", ".join(f"{y}: {n}" for y, n in f[f["is_forest"]].groupby(f["date"].dt.year).size().items()))


if __name__ == "__main__":
    cfg = load_config(sys.argv[1])
    det, days = build(cfg, sys.argv[2] if len(sys.argv) > 2 else None)
    report(det, days, cfg)
