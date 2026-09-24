import networkx as nx

import graph_data


def test_load_graph_returns_populated_networkx_graph():
    g = graph_data.load_graph()
    assert isinstance(g, nx.Graph)
    assert g.number_of_nodes() > 0
    assert g.number_of_edges() > 0
    # spot-check one edge has the fields exodus.py/graph_data.py rely on
    u, v, data = next(iter(g.edges(data=True)))
    assert "distance_km" in data and "base_time_min" in data and "highway" in data


def test_nearest_node_picks_closest():
    g = nx.Graph()
    g.add_node("far", lat=10.0, lon=10.0)
    g.add_node("near", lat=0.01, lon=0.01)
    g.add_node("nearest", lat=0.001, lon=0.001)
    result = graph_data.nearest_node(g, 0.0, 0.0)
    assert result == "nearest"


def test_load_hotspot_event_defaults_to_seeded(monkeypatch):
    monkeypatch.delenv("AGNIMARG_FIRMS_MAP_KEY", raising=False)
    event = graph_data.load_hotspot_event()
    assert event["label"] == "SEEDED DEMO EVENT — not a live FIRMS feed"
    assert len(event["hotspots"]) > 0
    assert "village_at_risk" in event and "shelter" in event


def test_load_hotspot_event_swaps_in_live_firms_data(monkeypatch):
    fake_hotspots = [{"id": "firms-0", "lat": 29.42, "lon": 79.43, "confidence": "high", "frp_mw": 50.0, "near": "live"}]
    monkeypatch.setattr(graph_data.firms, "fetch_live_hotspots", lambda *a, **kw: fake_hotspots)
    event = graph_data.load_hotspot_event()
    assert event["label"] == "LIVE NASA FIRMS FEED"
    assert event["hotspots"] == fake_hotspots
    # village/shelter/scenario weather stay from the seeded file even in live mode
    assert "village_at_risk" in event


def test_load_hotspot_event_falls_back_if_firms_raises(monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("simulated FIRMS outage")

    monkeypatch.setattr(graph_data.firms, "fetch_live_hotspots", boom)
    event = graph_data.load_hotspot_event()
    assert event["label"] == "SEEDED DEMO EVENT — not a live FIRMS feed"
