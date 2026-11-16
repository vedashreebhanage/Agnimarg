"""Terrain features per 1 km grid cell from the Copernicus DEM (30 m).

For every cell: mean elevation, elevation spread (ruggedness), mean slope, and mean aspect
expressed as northness and eastness. Aspect is the compass direction a slope faces; it is stored
as two numbers because an angle wraps around (359 degrees and 1 degree are nearly the same).
northness = +1 for a north-facing slope, -1 for south-facing; eastness = +1 east, -1 west.

Raw tiles are only read. Each tile is processed in strips to keep memory use low.

Usage:  python -m imagery.terrain config/uttarakhand.yaml
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import rasterio
import yaml
from pyproj import Geod, Transformer

from imagery.grid import cell_index, load_config

STRIP = 600  # DEM rows converted to grid coordinates at a time


def slope_aspect(z: np.ndarray, dx_m: np.ndarray, dy_m: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Slope (degrees), northness and eastness for an elevation array.

    z      rows run north to south, columns west to east
    dx_m   east-west pixel size in metres, one value per row (it shrinks towards the poles)
    dy_m   north-south pixel size in metres
    """
    d_row, d_col = np.gradient(z.astype(np.float64))
    dz_east = d_col / dx_m[:, None]
    dz_north = -d_row / dy_m                      # row index grows southwards
    steep = np.hypot(dz_east, dz_north)
    slope = np.degrees(np.arctan(steep))
    with np.errstate(invalid="ignore", divide="ignore"):
        northness = np.where(steep > 0, -dz_north / steep, 0.0)   # the slope faces downhill
        eastness = np.where(steep > 0, -dz_east / steep, 0.0)
    return slope, northness, eastness


def build(cfg: dict, out_dir: str | None = None) -> pd.DataFrame:
    out_dir = out_dir or cfg["output_dir"]
    grid = pd.read_parquet(os.path.join(cfg["output_dir"], "grid.parquet"), columns=["cell_id"])
    with open(os.path.join(cfg["output_dir"], "grid_meta.yaml"), encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    n = meta["nrow"] * meta["ncol"]
    sums = {k: np.zeros(n) for k in ("elev", "elev2", "slope", "north", "east")}
    count = np.zeros(n, dtype=np.int64)
    to_grid = Transformer.from_crs(4326, meta["crs"], always_xy=True)
    geod = Geod(ellps="WGS84")

    tiles = sorted(glob.glob(os.path.join(cfg["terrain"]["source_dir"], "*_DEM.tif")))
    if not tiles:
        raise FileNotFoundError("no DEM tiles found")
    for tile in tiles:
        with rasterio.open(tile) as src:
            if src.crs.to_epsg() != 4326:
                raise ValueError(f"{tile}: expected EPSG:4326, got {src.crs}")
            z = src.read(1)
            t = src.transform
            lons = t.c + (np.arange(src.width) + 0.5) * t.a
            lats = t.f + (np.arange(src.height) + 0.5) * t.e
        # True pixel size in metres at each row's latitude
        _, _, dx = geod.inv(np.full_like(lats, lons[0]), lats, np.full_like(lats, lons[0] + abs(t.a)), lats)
        _, _, dy = geod.inv(lons[0], lats[0], lons[0], lats[0] + abs(t.e))
        slope, north, east = slope_aspect(z, np.asarray(dx), float(dy))
        for r in range(0, len(lats), STRIP):
            sl = slice(r, min(r + STRIP, len(lats)))
            LON, LAT = np.meshgrid(lons, lats[sl])
            x, y = to_grid.transform(LON.ravel(), LAT.ravel())
            row, col, ok = cell_index(x, y, meta["x0"], meta["y0"], meta["cell_size_m"], meta["ncol"], meta["nrow"])
            idx = (row * meta["ncol"] + col)[ok]
            zz = z[sl].ravel()[ok].astype(np.float64)
            count += np.bincount(idx, minlength=n)
            sums["elev"] += np.bincount(idx, weights=zz, minlength=n)
            sums["elev2"] += np.bincount(idx, weights=zz * zz, minlength=n)
            sums["slope"] += np.bincount(idx, weights=slope[sl].ravel()[ok], minlength=n)
            sums["north"] += np.bincount(idx, weights=north[sl].ravel()[ok], minlength=n)
            sums["east"] += np.bincount(idx, weights=east[sl].ravel()[ok], minlength=n)

    ids = grid["cell_id"].to_numpy()
    c = count[ids].astype(np.float64)
    if (c == 0).any():
        raise ValueError(f"{int((c == 0).sum())} grid cells have no DEM pixels")
    mean = sums["elev"][ids] / c
    out = pd.DataFrame({
        "cell_id": ids,
        "dem_pixels": count[ids].astype(np.int32),
        "elev_mean_m": mean.astype(np.float32),
        "elev_std_m": np.sqrt(np.maximum(sums["elev2"][ids] / c - mean * mean, 0)).astype(np.float32),
        "slope_mean_deg": (sums["slope"][ids] / c).astype(np.float32),
        "northness": (sums["north"][ids] / c).astype(np.float32),
        "eastness": (sums["east"][ids] / c).astype(np.float32),
    })
    os.makedirs(out_dir, exist_ok=True)
    out.to_parquet(os.path.join(out_dir, "terrain.parquet"), index=False)
    return out


if __name__ == "__main__":
    cfg = load_config(sys.argv[1])
    df = build(cfg, sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"cells: {len(df)}; DEM pixels per cell: {df['dem_pixels'].min()} to {df['dem_pixels'].max()}")
    print(df.drop(columns=["cell_id", "dem_pixels"]).describe().loc[["min", "50%", "mean", "max"]].round(2).to_string())
