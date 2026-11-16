"""Human-factor features per 1 km grid cell that do not change from day to day.

  population          people living in the cell (WorldPop 2020)
  dist_road_m         distance to the nearest motorable road (OpenStreetMap)
  dist_path_m         distance to the nearest road, track or footpath of any kind
  dist_settlement_m   distance to the nearest named city, town, village or hamlet

Distances are measured on a 100 m raster and averaged over the cell. They are capped by what
OpenStreetMap contains: unmapped roads make distances too long, and the extract covers India only,
so cells near the Nepal and China borders may be closer to a road than recorded.

Known limit: one snapshot (roads as mapped in 2026, population 2020) is used for every year.

Usage:  python -m ml.features_static config/uttarakhand.yaml
"""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
import tempfile

import numpy as np
import osmium
import pandas as pd
import rasterio
import yaml
from affine import Affine
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from scipy.ndimage import distance_transform_edt
from shapely import linestrings, transform as shp_transform

from imagery.grid import cell_index, load_config

SUB = 10          # sub-cells per grid cell side (1 km / 10 = 100 m)
POP_STRIP = 400   # population rows read at a time
WAY_BATCH = 20000


def grid_bounds_lonlat(meta: dict, margin_deg: float = 0.05) -> tuple[float, float, float, float]:
    """Longitude/latitude box that contains the whole grid, with a small margin."""
    x1 = meta["x0"] + meta["ncol"] * meta["cell_size_m"]
    y1 = meta["y0"] + meta["nrow"] * meta["cell_size_m"]
    xs = np.array([meta["x0"], x1, meta["x0"], x1, (meta["x0"] + x1) / 2, (meta["x0"] + x1) / 2])
    ys = np.array([meta["y0"], meta["y0"], y1, y1, meta["y0"], y1])
    lon, lat = Transformer.from_crs(meta["crs"], 4326, always_xy=True).transform(xs, ys)
    return lon.min() - margin_deg, lat.min() - margin_deg, lon.max() + margin_deg, lat.max() + margin_deg


def population_per_cell(path: str, meta: dict) -> np.ndarray:
    n = meta["nrow"] * meta["ncol"]
    pop = np.zeros(n)
    to_grid = Transformer.from_crs(4326, meta["crs"], always_xy=True)
    west, south, east, north = grid_bounds_lonlat(meta)
    with rasterio.open(path) as src:
        if src.crs.to_epsg() != 4326:
            raise ValueError(f"{path}: expected EPSG:4326, got {src.crs}")
        win = from_bounds(west, south, east, north, src.transform).round_offsets().round_lengths()
        r0, c0, r1, c1 = int(win.row_off), int(win.col_off), int(win.row_off + win.height), int(win.col_off + win.width)
        t = src.transform
        lons = t.c + (np.arange(c0, c1) + 0.5) * t.a
        for r in range(r0, r1, POP_STRIP):
            h = min(POP_STRIP, r1 - r)
            data = src.read(1, window=Window(c0, r, c1 - c0, h)).astype(np.float64)
            data[(data == src.nodata) | ~np.isfinite(data) | (data < 0)] = 0.0   # no data = unsettled
            lats = t.f + (np.arange(r, r + h) + 0.5) * t.e
            LON, LAT = np.meshgrid(lons, lats)
            x, y = to_grid.transform(LON.ravel(), LAT.ravel())
            row, col, ok = cell_index(x, y, meta["x0"], meta["y0"], meta["cell_size_m"], meta["ncol"], meta["nrow"])
            pop += np.bincount((row * meta["ncol"] + col)[ok], weights=data.ravel()[ok], minlength=n)
    return pop


def mean_distance_per_cell(mask: np.ndarray, sub_size_m: float) -> np.ndarray:
    """mask: fine raster, True where a feature is. Returns mean distance (m) per grid cell, row-major
    with row 0 at the bottom (south), matching cell_id order."""
    if not mask.any():
        raise ValueError("no features found; cannot compute distances")
    dist = distance_transform_edt(~mask) * sub_size_m
    nr, nc = mask.shape[0] // SUB, mask.shape[1] // SUB
    cell = dist.reshape(nr, SUB, nc, SUB).mean(axis=(1, 3))
    return cell[::-1].ravel()          # raster row 0 is the north edge; grid row 0 is the south edge


def _osm_worker(path: str, bounds, road_classes: dict, place_types: list, tmp: str) -> None:
    """Runs in a separate process: reads the OSM file and saves what is needed to tmp/osm.npz."""
    west, south, east, north = bounds
    groups = list(road_classes)
    group_of = {v: i for i, g in enumerate(groups) for v in road_classes[g]}
    coords, lengths, codes, places = [], [], [], []
    fp = (osmium.FileProcessor(path, osmium.osm.NODE | osmium.osm.WAY)
          .with_locations(f"sparse_file_array,{os.path.join(tmp, 'nodes.idx')}")
          .with_filter(osmium.filter.KeyFilter("highway", "place")))
    for o in fp:
        if o.is_node():
            if o.tags.get("place") in place_types and west <= o.lon <= east and south <= o.lat <= north:
                places.append((o.lon, o.lat))
        elif o.is_way():
            g = group_of.get(o.tags.get("highway"))
            if g is None:
                continue
            pts = [(nd.lon, nd.lat) for nd in o.nodes if nd.location.valid()]
            if len(pts) < 2:
                continue
            a = np.asarray(pts)
            if a[:, 0].max() < west or a[:, 0].min() > east or a[:, 1].max() < south or a[:, 1].min() > north:
                continue
            coords.append(a); lengths.append(len(a)); codes.append(g)
    np.savez(os.path.join(tmp, "osm.npz"), coords=np.concatenate(coords), lengths=np.asarray(lengths),
             codes=np.asarray(codes), places=np.asarray(places))


def read_osm(path: str, bounds: tuple[float, float, float, float], road_classes: dict, place_types: list[str]):
    """Return (ways, places): ways is a list of (class_group, lon/lat array); places a lon/lat array.

    The file is read in a separate process. The reader keeps a large temporary index file open
    until its process ends, and Windows cannot delete an open file; ending the process first lets
    the temporary folder be removed cleanly.
    """
    with tempfile.TemporaryDirectory() as tmp:
        proc = mp.get_context("spawn").Process(target=_osm_worker, args=(path, bounds, road_classes, place_types, tmp))
        proc.start()
        proc.join()
        if proc.exitcode != 0:
            raise RuntimeError(f"reading {path} failed (exit code {proc.exitcode})")
        with np.load(os.path.join(tmp, "osm.npz")) as z:
            coords, lengths, codes, places = z["coords"], z["lengths"], z["codes"], z["places"]
    groups = list(road_classes)
    ends = np.cumsum(lengths)
    ways = [(groups[c], coords[e - n:e]) for c, n, e in zip(codes, lengths, ends)]
    return ways, places


def build(cfg: dict, out_dir: str | None = None) -> pd.DataFrame:
    out_dir = out_dir or cfg["output_dir"]
    grid = pd.read_parquet(os.path.join(cfg["output_dir"], "grid.parquet"), columns=["cell_id"])
    with open(os.path.join(cfg["output_dir"], "grid_meta.yaml"), encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    st = cfg["static"]
    ids = grid["cell_id"].to_numpy()

    pop = population_per_cell(st["population_file"], meta)

    sub = meta["cell_size_m"] / SUB
    shape = (meta["nrow"] * SUB, meta["ncol"] * SUB)
    top = meta["y0"] + meta["nrow"] * meta["cell_size_m"]
    fine = Affine(sub, 0, meta["x0"], 0, -sub, top)
    to_grid = Transformer.from_crs(4326, meta["crs"], always_xy=True)

    ways, places = read_osm(st["osm_file"], grid_bounds_lonlat(meta), st["road_classes"], st["place_types"])
    masks = {g: np.zeros(shape, dtype=bool) for g in st["road_classes"]}
    n_ways = {g: 0 for g in st["road_classes"]}
    for g in st["road_classes"]:
        sel = [a for gg, a in ways if gg == g]
        n_ways[g] = len(sel)
        for i in range(0, len(sel), WAY_BATCH):
            lines = [shp_transform(linestrings(a), lambda c: np.column_stack(to_grid.transform(c[:, 0], c[:, 1])))
                     for a in sel[i:i + WAY_BATCH]]
            masks[g] |= rasterize(lines, out_shape=shape, transform=fine, all_touched=True, dtype="uint8").astype(bool)
    del ways

    px, py = to_grid.transform(places[:, 0], places[:, 1])
    prow, pcol = np.floor((top - py) / sub).astype(int), np.floor((px - meta["x0"]) / sub).astype(int)
    inside = (prow >= 0) & (prow < shape[0]) & (pcol >= 0) & (pcol < shape[1])
    place_mask = np.zeros(shape, dtype=bool)
    place_mask[prow[inside], pcol[inside]] = True

    motor = masks["motorable"]
    anyway = motor | masks["path"]
    out = pd.DataFrame({
        "cell_id": ids,
        "population": pop[ids].astype(np.float32),
        "dist_road_m": mean_distance_per_cell(motor, sub)[ids].astype(np.float32),
        "dist_path_m": mean_distance_per_cell(anyway, sub)[ids].astype(np.float32),
        "dist_settlement_m": mean_distance_per_cell(place_mask, sub)[ids].astype(np.float32),
    })
    out.attrs.update(n_ways=n_ways, n_places=int(inside.sum()))
    os.makedirs(out_dir, exist_ok=True)
    out.to_parquet(os.path.join(out_dir, "static.parquet"), index=False)
    return out


if __name__ == "__main__":
    cfg = load_config(sys.argv[1])
    df = build(cfg, sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"cells: {len(df)}; OSM ways used: {df.attrs['n_ways']}; settlements: {df.attrs['n_places']}")
    print(f"population total: {df['population'].sum():,.0f}; cells with no residents: {(df['population'] == 0).mean():.1%}")
    print(df.drop(columns=["cell_id"]).describe().loc[["min", "50%", "mean", "max"]].round(1).to_string())
