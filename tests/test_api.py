"""Integration tests against the real FastAPI app, using the real road-graph
data checked into backend/data/. Slower than the unit tests (loads the full
graph once per test session) but exercises the actual HTTP surface."""
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["graph_nodes"] > 0
    assert data["graph_edges"] > 0


def test_get_weather_scenario_mode(client):
    r = client.get("/api/weather?mode=scenario")
    assert r.status_code == 200
    data = r.json()
    assert data["source"].startswith("seeded fire-season scenario")


def test_get_state(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    data = r.json()
    assert "hotspots" in data
    assert "village_at_risk" in data
    assert "shelter" in data
    assert len(data["graph_edges"]) > 0


def test_simulate_scenario_mode(client):
    r = client.post("/api/simulate?mode=scenario")
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["signature"]
    assert "baseline_route" in data and "safe_route" in data


def test_tamper_demo_rejects(client):
    client.post("/api/simulate?mode=scenario")  # ensure there's a last simulation
    r = client.post("/api/tamper-demo")
    assert r.status_code == 200
    assert r.json()["rejected"] is True


def _login(client, username, password):
    r = client.post("/api/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return r.json()["token"]


def test_login_rejects_bad_credentials(client):
    r = client.post("/api/login", json={"username": "authority1", "password": "wrong"})
    assert r.status_code == 401


def test_dispatch_approve_requires_auth_header(client):
    client.post("/api/simulate?mode=scenario")
    r = client.post("/api/dispatch/approve")  # no Authorization header at all
    assert r.status_code == 401


def test_dispatch_approve_denies_citizen(client):
    client.post("/api/simulate?mode=scenario")
    token = _login(client, "citizen1", "demo-citizen-pass")
    r = client.post("/api/dispatch/approve", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_dispatch_approve_allows_authority(client):
    client.post("/api/simulate?mode=scenario")
    token = _login(client, "authority1", "demo-authority-pass")
    r = client.post("/api/dispatch/approve", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["approved"] is True


def test_dispatch_approve_rejects_forged_role_in_body(client):
    """Regression test for the exact gap this section fixed: a client can no
    longer just claim role="authority" in the request body — the endpoint
    takes no such field, and an authenticated-but-citizen token still gets 403."""
    client.post("/api/simulate?mode=scenario")
    token = _login(client, "citizen1", "demo-citizen-pass")
    r = client.post(
        "/api/dispatch/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "authority", "actor": "forged"},  # ignored — no such field on the endpoint
    )
    assert r.status_code == 403


def test_audit_log_grows(client):
    before = len(client.get("/api/audit-log").json()["entries"])
    client.post("/api/simulate?mode=scenario")
    after = len(client.get("/api/audit-log").json()["entries"])
    assert after > before
