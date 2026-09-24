"""EXODUS — the response-orchestration slice of tonight's demo.

Verifies the HMAC signature on SENTINEL's threat-cone payload before touching it
(rejects tampered/unsigned payloads — this is demoed live, not just claimed).
Then re-costs the real OSM road graph: edges inside the nearest (1h) cone are
blocked outright, edges inside the 3h/6h cones get a rising cost penalty, and a
Dijkstra shortest-time path is recomputed from the at-risk village to the shelter
— mirrors the "dynamic re-costed routing" that the comparative-study doc calls
out as AGNIMARG's differentiator over systems that stop at detection/prediction.
"""
import copy

import networkx as nx

from sentinel import verify_payload

BLOCK_PENALTY_MULTIPLIER = 1000  # effectively impassable, without deleting the edge
RING_PENALTY = {"1h": None, "3h": 8.0, "6h": 3.0}  # None => full block


def _point_in_polygon(lat, lon, polygon):
    """Ray-casting point-in-polygon test. polygon: list of [lat, lon] (closed or not)."""
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _edge_ring_penalty(g, u, v, cones_by_hotspot):
    """Return (blocked: bool, penalty_multiplier: float) for edge u-v against all cones."""
    pu, pv = g.nodes[u], g.nodes[v]
    mid_lat = (pu["lat"] + pv["lat"]) / 2
    mid_lon = (pu["lon"] + pv["lon"]) / 2

    blocked = False
    max_penalty = 1.0
    for cones in cones_by_hotspot.values():
        for ring_key, ring in cones.items():
            if not _point_in_polygon(mid_lat, mid_lon, ring["polygon"]):
                continue
            penalty = RING_PENALTY[ring_key]
            if penalty is None:
                blocked = True
            else:
                max_penalty = max(max_penalty, penalty)
    return blocked, max_penalty


def recost_graph(g: nx.Graph, cones_by_hotspot: dict) -> nx.Graph:
    g2 = g.copy()
    for u, v, data in g2.edges(data=True):
        blocked, penalty = _edge_ring_penalty(g2, u, v, cones_by_hotspot)
        if blocked:
            data["cost_min"] = data["base_time_min"] * BLOCK_PENALTY_MULTIPLIER
            data["blocked"] = True
        else:
            data["cost_min"] = data["base_time_min"] * penalty
            data["blocked"] = False
    return g2


def _route_latlon(g: nx.Graph, node_path: list) -> list:
    return [[g.nodes[n]["lat"], g.nodes[n]["lon"]] for n in node_path]


def compute_route(g: nx.Graph, origin_node, dest_node, weight="base_time_min"):
    """Routes by `weight` (which may include a risk penalty, to steer the path
    away from danger) but always reports ETA as actual predicted drive time
    (base_time_min summed over the chosen path) — the risk penalty should change
    *which* road is picked, not be reported to the user as if it were travel time."""
    path = nx.shortest_path(g, origin_node, dest_node, weight=weight)
    actual_time_min = sum(
        g[u][v]["base_time_min"] for u, v in zip(path, path[1:])
    )
    return {"path_latlon": _route_latlon(g, path), "eta_min": round(actual_time_min, 1), "node_count": len(path)}


class SignatureRejected(Exception):
    pass


def process_signed_threat(g: nx.Graph, signed_payload: dict, origin_node, dest_node) -> dict:
    """The RBAC/security boundary: EXODUS only acts on a payload whose signature
    verifies. Called by both the normal simulate flow and the tamper-demo endpoint."""
    payload, signature = signed_payload["payload"], signed_payload["signature"]
    if not verify_payload(payload, signature):
        raise SignatureRejected("HMAC signature verification failed — threat-cone payload rejected.")

    recosted = recost_graph(g, payload["cones_by_hotspot"])
    baseline_route = compute_route(g, origin_node, dest_node, weight="base_time_min")
    safe_route = compute_route(recosted, origin_node, dest_node, weight="cost_min")

    blocked_edges = sum(1 for _, _, d in recosted.edges(data=True) if d["blocked"])
    return {
        "baseline_route": baseline_route,
        "safe_route": safe_route,
        "blocked_edge_count": blocked_edges,
        "rerouted": baseline_route["path_latlon"] != safe_route["path_latlon"],
    }
