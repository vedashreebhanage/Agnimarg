"""
One-time offline data-prep step for the AGNIMARG software-only prototype demo.

Pulls REAL OpenStreetMap road network + place/amenity data for the demo region
(Nainital, Uttarakhand — matches the "heavily forested states" the project's own
comparative study calls out) via the public Overpass API, and writes a compact
graph the FastAPI backend loads at runtime.

Fire hotspots are NOT pulled here: NASA FIRMS requires a personal MAP_KEY
(https://firms.modaps.eosdis.nasa.gov/api/map_key/, free, instant). Until one is
supplied, seed_hotspots.py writes a seeded historical-style event instead — this
mirrors the "Reproducible Demo Plan" in the project's own master blueprint, which
recommends replaying a real historical fire as "live" for a scheduled demo rather
than depending on a fire actually burning at presentation time.

Run: python scripts/fetch_data.py
"""
import json
import math
import os
import time

import requests

BBOX = (29.32, 79.40, 29.44, 79.52)  # south, west, north, east — Nainital, Uttarakhand
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "data")
HEADERS = {"User-Agent": "agnimarg-prototype/1.0 (college mid-sem review demo)"}


def overpass(query: str, retries: int = 4) -> dict:
    """The public Overpass API is frequently overloaded (504s); retry a few times
    before giving up rather than failing the whole data-prep step on one blip."""
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                headers=HEADERS,
                timeout=90,
            )
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last_err = str(e)
        print(f"  Overpass attempt {attempt + 1} failed ({last_err}), retrying ...")
        time.sleep(6)
    raise RuntimeError(f"Overpass API failed after {retries} attempts: {last_err}")


def fetch_roads():
    s, w, n, e = BBOX
    q = f"""
    [out:json][timeout:40];
    way["highway"]["highway"!~"footway|path|steps|cycleway|pedestrian|track"]({s},{w},{n},{e});
    (._;>;);
    out body;
    """
    data = overpass(q)
    nodes = {}
    ways = []
    for el in data["elements"]:
        if el["type"] == "node":
            nodes[el["id"]] = {"lat": el["lat"], "lon": el["lon"]}
        elif el["type"] == "way":
            ways.append({
                "id": el["id"],
                "nodes": el["nodes"],
                "name": el.get("tags", {}).get("name", ""),
                "highway": el.get("tags", {}).get("highway", ""),
            })
    return nodes, ways


def fetch_places():
    s, w, n, e = BBOX
    q = f"""
    [out:json][timeout:40];
    (
      node["place"~"village|town|hamlet"]({s},{w},{n},{e});
      node["amenity"~"hospital|school|police"]({s},{w},{n},{e});
    );
    out body;
    """
    data = overpass(q)
    places = []
    for el in data["elements"]:
        if el["type"] != "node":
            continue
        tags = el.get("tags", {})
        places.append({
            "id": el["id"],
            "lat": el["lat"],
            "lon": el["lon"],
            "name": tags.get("name", "Unnamed"),
            "kind": tags.get("place") or tags.get("amenity"),
        })
    return places


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def build_graph(nodes, ways):
    """Collapse OSM ways into a simple weighted edge list keyed by node id."""
    used_nodes = set()
    edges = []
    for way in ways:
        seq = way["nodes"]
        for a_id, b_id in zip(seq, seq[1:]):
            if a_id not in nodes or b_id not in nodes:
                continue
            used_nodes.add(a_id)
            used_nodes.add(b_id)
            dist_km = haversine_km(nodes[a_id], nodes[b_id])
            if dist_km <= 0:
                continue
            edges.append({
                "from": a_id, "to": b_id,
                "distance_km": round(dist_km, 4),
                "highway": way["highway"], "way_name": way["name"],
            })
    graph_nodes = [{"id": nid, **nodes[nid]} for nid in used_nodes]
    return graph_nodes, edges


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Fetching OSM road network for Nainital, Uttarakhand ...")
    nodes, ways = fetch_roads()
    graph_nodes, edges = build_graph(nodes, ways)
    print(f"  {len(graph_nodes)} nodes, {len(edges)} edges, {len(ways)} ways")

    print("Fetching villages/towns + shelters (hospitals/schools) ...")
    places = fetch_places()
    print(f"  {len(places)} places")

    with open(os.path.join(OUT_DIR, "road_graph.json"), "w", encoding="utf-8") as f:
        json.dump({"bbox": BBOX, "nodes": graph_nodes, "edges": edges}, f)

    with open(os.path.join(OUT_DIR, "places.json"), "w", encoding="utf-8") as f:
        json.dump({"bbox": BBOX, "places": places}, f, ensure_ascii=False)

    print("Wrote backend/data/road_graph.json and backend/data/places.json")


if __name__ == "__main__":
    main()
