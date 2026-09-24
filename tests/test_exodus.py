import networkx as nx
import pytest

import exodus
import sentinel


def test_point_in_polygon_inside_and_outside():
    square = [[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]
    assert exodus._point_in_polygon(1, 1, square) is True
    assert exodus._point_in_polygon(5, 5, square) is False


def _tiny_graph():
    """A(0,0) -- B(0,1) -- C(0,2), plus a longer detour A -- D(1,1) -- C,
    so re-costing has a real alternative path to route around."""
    g = nx.Graph()
    g.add_node("A", lat=0.0, lon=0.0)
    g.add_node("B", lat=0.0, lon=1.0)
    g.add_node("C", lat=0.0, lon=2.0)
    g.add_node("D", lat=1.0, lon=1.0)
    g.add_edge("A", "B", distance_km=1.0, base_time_min=2.0, highway="residential", way_name="")
    g.add_edge("B", "C", distance_km=1.0, base_time_min=2.0, highway="residential", way_name="")
    g.add_edge("A", "D", distance_km=1.5, base_time_min=3.0, highway="residential", way_name="")
    g.add_edge("D", "C", distance_km=1.5, base_time_min=3.0, highway="residential", way_name="")
    return g


def test_recost_graph_blocks_edge_inside_1h_ring():
    g = _tiny_graph()
    # a cone polygon (square) that covers the A-B edge midpoint (0, 0.5) but not D
    cone_covering_ab = [[-1, -1], [-1, 1], [1, 1], [1, -1], [-1, -1]]
    cones_by_hotspot = {"h1": {"1h": {"polygon": cone_covering_ab}}}
    recosted = exodus.recost_graph(g, cones_by_hotspot)
    assert recosted["A"]["B"]["blocked"] is True


def test_recost_graph_leaves_unaffected_edges_alone():
    g = _tiny_graph()
    far_away_cone = [[50, 50], [50, 51], [51, 51], [51, 50], [50, 50]]
    cones_by_hotspot = {"h1": {"1h": {"polygon": far_away_cone}}}
    recosted = exodus.recost_graph(g, cones_by_hotspot)
    assert all(not d["blocked"] for _, _, d in recosted.edges(data=True))


def test_compute_route_basic():
    g = _tiny_graph()
    result = exodus.compute_route(g, "A", "C", weight="base_time_min")
    assert result["path_latlon"][0] == [0.0, 0.0]
    assert result["path_latlon"][-1] == [0.0, 2.0]
    assert result["eta_min"] == pytest.approx(4.0)  # A-B-C is the shortest by time


def test_process_signed_threat_reroutes_around_blocked_edge():
    g = _tiny_graph()
    # Force-block only the direct A-B-C path (midpoints at lat 0.0) without
    # touching the A-D-C detour (midpoints at lat 0.5), so a real alternative
    # route exists for EXODUS to pick.
    cone_covering_ab_only = [[-0.2, -0.5], [-0.2, 1.5], [0.2, 1.5], [0.2, -0.5], [-0.2, -0.5]]
    payload = {"cones_by_hotspot": {"h1": {"1h": {"polygon": cone_covering_ab_only}}}}
    signature = sentinel.sign_payload(payload)
    signed = {"payload": payload, "signature": signature}

    result = exodus.process_signed_threat(g, signed, "A", "C")
    assert result["blocked_edge_count"] >= 1
    assert result["rerouted"] is True
    assert result["safe_route"]["path_latlon"] == [[0.0, 0.0], [1.0, 1.0], [0.0, 2.0]]


def test_process_signed_threat_rejects_tampered_payload():
    g = _tiny_graph()
    payload = {"cones_by_hotspot": {}}
    signature = sentinel.sign_payload(payload)
    tampered = {"payload": {"cones_by_hotspot": {"injected": "data"}}, "signature": signature}

    with pytest.raises(exodus.SignatureRejected):
        exodus.process_signed_threat(g, tampered, "A", "C")
