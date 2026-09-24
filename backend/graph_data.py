"""Loads the offline OSM road-graph extract (scripts/fetch_data.py output) into
a NetworkX graph, and the seeded/live hotspot + village + shelter data."""
import json
import math
import os

import networkx as nx

import firms

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

BASE_SPEED_KMH = {
    "trunk": 60, "primary": 50, "secondary": 40, "tertiary": 30,
    "unclassified": 25, "residential": 20, "service": 15, "track": 15,
}
DEFAULT_SPEED_KMH = 25
SOURCE_BBOX_NOTE = "VIIRS_SNPP_NRT, Nainital/Uttarakhand bbox"


def _edge_time_min(distance_km: float, highway: str) -> float:
    speed = BASE_SPEED_KMH.get(highway, DEFAULT_SPEED_KMH)
    return (distance_km / speed) * 60


def load_graph() -> nx.Graph:
    with open(os.path.join(DATA_DIR, "road_graph.json"), encoding="utf-8") as f:
        raw = json.load(f)

    g = nx.Graph()
    for n in raw["nodes"]:
        g.add_node(n["id"], lat=n["lat"], lon=n["lon"])
    for e in raw["edges"]:
        base_time = _edge_time_min(e["distance_km"], e["highway"])
        g.add_edge(
            e["from"], e["to"],
            distance_km=e["distance_km"],
            base_time_min=base_time,
            highway=e["highway"],
            way_name=e["way_name"],
        )
    return g


def nearest_node(g: nx.Graph, lat: float, lon: float) -> int:
    best_id, best_d = None, math.inf
    for nid, attrs in g.nodes(data=True):
        d = (attrs["lat"] - lat) ** 2 + (attrs["lon"] - lon) ** 2
        if d < best_d:
            best_d, best_id = d, nid
    return best_id


def load_hotspot_event() -> dict:
    """Returns the seeded demo event by default. If AGNIMARG_FIRMS_MAP_KEY is
    set, tries a live FIRMS pull over the same bbox first and, if it returns
    any hotspots, swaps them in — village/shelter and the fire-season scenario
    weather stay from the seeded file either way, since those are fixed demo-
    region facts, not something FIRMS provides."""
    with open(os.path.join(DATA_DIR, "hotspots.json"), encoding="utf-8") as f:
        seeded = json.load(f)

    with open(os.path.join(DATA_DIR, "road_graph.json"), encoding="utf-8") as f:
        south, west, north, east = json.load(f)["bbox"]

    try:
        live = firms.fetch_live_hotspots(south, west, north, east)
    except Exception:
        live = None  # a configured-but-failing key shouldn't crash the demo

    if live:
        seeded = {
            **seeded,
            "label": "LIVE NASA FIRMS FEED",
            "note": f"Live active-fire hotspots from NASA FIRMS ({SOURCE_BBOX_NOTE}).",
            "hotspots": live,
        }
    return seeded


def load_places() -> list:
    with open(os.path.join(DATA_DIR, "places.json"), encoding="utf-8") as f:
        return json.load(f)["places"]
