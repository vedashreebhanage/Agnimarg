"""Build the 1 km analysis grid and land-cover fractions for one region.

For every grid cell this records its position, whether its centre lies inside the region boundary,
and what share of the cell is tree cover, shrubland, grassland, cropland and built-up land
(from ESA WorldCover 10 m). Cells with enough tree + shrub cover are flagged `is_forest`.

Raw files are only read, never changed. WorldCover tiles are processed in small blocks so the
script runs on a PC with little free memory.

Usage:  python -m imagery.grid config/uttarakhand.yaml
"""
from __future__ import annotations

import glob
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import yaml
from pyproj import Transformer
from rasterio.windows import Window, from_bounds
from shapely import contains_xy

BLOCK = 2048  # pixels per side read at a time (about 4 million pixels, ~20 km at 10 m)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def region_polygon(cfg: dict) -> gpd.GeoSeries:
    """Region boundary as a one-row GeoSeries in longitude/latitude (EPSG:4326)."""
    adm = gpd.read_file(cfg["region"]["boundary_file"])
    sel = adm[adm["shapeISO"] == cfg["region"]["boundary_iso"]]
    if len(sel) != 1:
        raise ValueError(f"expected exactly one boundary for {cfg['region']['boundary_iso']}, got {len(sel)}")
    return sel.geometry.to_crs(4326)


def build_grid(cfg: dict) -> pd.DataFrame:
    crs, size = cfg["grid"]["crs"], cfg["grid"]["cell_size_m"]
    poly_ll = region_polygon(cfg)
    poly = poly_ll.to_crs(crs)
    minx, miny, maxx, maxy = poly.total_bounds
    # Snap the grid origin to whole multiples of the cell size so it is reproducible.
    x0, y0 = np.floor(minx / size) * size, np.floor(miny / size) * size
    ncol, nrow = int(np.ceil((maxx - x0) / size)), int(np.ceil((maxy - y0) / size))

    col, row = np.meshgrid(np.arange(ncol), np.arange(nrow))
    col, row = col.ravel(), row.ravel()
    x, y = x0 + (col + 0.5) * size, y0 + (row + 0.5) * size
    lon, lat = Transformer.from_crs(crs, 4326, always_xy=True).transform(x, y)
    in_region = contains_xy(poly.iloc[0], x, y)

    # Count WorldCover pixels per cell, by class.
    classes: dict[str, int] = cfg["land_cover"]["classes"]
    counts = {name: np.zeros(nrow * ncol, dtype=np.int64) for name in classes}
    total = np.zeros(nrow * ncol, dtype=np.int64)
    to_grid = Transformer.from_crs(4326, crs, always_xy=True)
    west, south, east, north = poly_ll.total_bounds
    pad = 0.02  # degrees; a little margin so edge cells are fully counted

    tiles = sorted(glob.glob(os.path.join(cfg["land_cover"]["source_dir"], "*_Map.tif")))
    if not tiles:
        raise FileNotFoundError("no WorldCover tiles found")
    for tile in tiles:
        with rasterio.open(tile) as src:
            if src.crs.to_epsg() != 4326:
                raise ValueError(f"{tile}: expected EPSG:4326, got {src.crs}")
            b = src.bounds
            w, s, e, n = max(west - pad, b.left), max(south - pad, b.bottom), min(east + pad, b.right), min(north + pad, b.top)
            if w >= e or s >= n:
                continue  # tile does not touch the region
            win = from_bounds(w, s, e, n, src.transform).round_offsets().round_lengths()
            r_start, c_start = int(win.row_off), int(win.col_off)
            r_end, c_end = min(r_start + int(win.height), src.height), min(c_start + int(win.width), src.width)
            for r in range(r_start, r_end, BLOCK):
                for c in range(c_start, c_end, BLOCK):
                    h, wd = min(BLOCK, r_end - r), min(BLOCK, c_end - c)
                    data = src.read(1, window=Window(c, r, wd, h))
                    # Pixel-centre coordinates of this block
                    lons = src.transform.c + (c + np.arange(wd) + 0.5) * src.transform.a
                    lats = src.transform.f + (r + np.arange(h) + 0.5) * src.transform.e
                    LON, LAT = np.meshgrid(lons, lats)
                    px, py = to_grid.transform(LON.ravel(), LAT.ravel())
                    ci = np.floor((px - x0) / size).astype(np.int64)
                    ri = np.floor((py - y0) / size).astype(np.int64)
                    ok = (ci >= 0) & (ci < ncol) & (ri >= 0) & (ri < nrow) & (data.ravel() != 0)  # 0 = no data
                    idx = ri[ok] * ncol + ci[ok]
                    vals = data.ravel()[ok]
                    total += np.bincount(idx, minlength=nrow * ncol)
                    for name, code in classes.items():
                        counts[name] += np.bincount(idx[vals == code], minlength=nrow * ncol)

    df = pd.DataFrame({
        "cell_id": (row * ncol + col).astype(np.int32), "row": row.astype(np.int32), "col": col.astype(np.int32),
        "x": x, "y": y, "lon": lon, "lat": lat, "in_region": in_region, "lc_pixels": total,
    })
    with np.errstate(invalid="ignore", divide="ignore"):
        for name in classes:
            df[f"frac_{name}"] = np.where(total > 0, counts[name] / total, np.nan).astype(np.float32)
    df = df[df["in_region"]].reset_index(drop=True)
    df["is_forest"] = (df["frac_tree"] + df["frac_shrub"]) >= cfg["land_cover"]["forest_min_fraction"]
    df.attrs.update(x0=float(x0), y0=float(y0), ncol=ncol, nrow=nrow, cell_size_m=size, crs=crs)
    return df


def main(config_path: str) -> None:
    cfg = load_config(config_path)
    df = build_grid(cfg)
    os.makedirs(cfg["output_dir"], exist_ok=True)
    out = os.path.join(cfg["output_dir"], "grid.parquet")
    df.to_parquet(out, index=False)
    with open(os.path.join(cfg["output_dir"], "grid_meta.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(dict(df.attrs), f)
    print(f"cells in region: {len(df)}")
    print(f"cells with no land-cover pixels: {int((df['lc_pixels'] == 0).sum())}")
    print(f"forest cells (tree+shrub >= {cfg['land_cover']['forest_min_fraction']}): {int(df['is_forest'].sum())}")
    print(f"mean fractions: " + ", ".join(f"{c[5:]}={df[c].mean():.3f}" for c in df.columns if c.startswith('frac_')))
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1])
