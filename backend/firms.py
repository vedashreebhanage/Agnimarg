"""Optional live NASA FIRMS active-fire hotspot feed.

Needs a free personal MAP_KEY (instant signup, no cost):
https://firms.modaps.eosdis.nasa.gov/api/map_key/

Set it as the AGNIMARG_FIRMS_MAP_KEY environment variable. If it's unset, or
the request fails, or no hotspots fall inside the demo bbox, the caller
(graph_data.load_hotspot_event) falls back to the seeded historical-style
event — this module never raises for the "no key" case, only for genuinely
unexpected failures once a key IS configured, so a misconfigured key fails
loudly rather than silently masquerading as "no live data available".
"""
import csv
import io
import os

import requests

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCE = "VIIRS_SNPP_NRT"


def _bbox_str(south: float, west: float, north: float, east: float) -> str:
    # FIRMS expects "west,south,east,north"
    return f"{west},{south},{east},{north}"


def fetch_live_hotspots(south: float, west: float, north: float, east: float, days: int = 1) -> list | None:
    """Returns a list of hotspot dicts in our internal schema, or None if no
    MAP_KEY is configured (the normal, expected case for this demo)."""
    map_key = os.environ.get("AGNIMARG_FIRMS_MAP_KEY")
    if not map_key:
        return None

    url = f"{FIRMS_BASE_URL}/{map_key}/{SOURCE}/{_bbox_str(south, west, north, east)}/{days}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return parse_firms_csv(r.text)


def parse_firms_csv(csv_text: str) -> list:
    """Parses the FIRMS CSV response into our hotspot schema. Pure function,
    tested independently of any network call — see tests/test_firms.py."""
    reader = csv.DictReader(io.StringIO(csv_text))
    hotspots = []
    for i, row in enumerate(reader):
        try:
            hotspots.append({
                "id": f"firms-{i}",
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
                "confidence": row.get("confidence", "unknown"),
                "frp_mw": float(row["frp"]) if row.get("frp") else None,
                "near": "NASA FIRMS live feed",
            })
        except (KeyError, ValueError):
            continue  # skip malformed rows rather than fail the whole feed
    return hotspots
