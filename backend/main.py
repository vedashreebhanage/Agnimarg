"""AGNIMARG software-only prototype — FastAPI backend.

Ties together INTAKE (graph_data + weather), SENTINEL (sentinel.py),
EXODUS (exodus.py) and INTERFACE (this file's API + audit log) for the
one-night mid-sem-review demo. Serves the static frontend too, so the whole
thing runs from a single `uvicorn backend.main:app` command with no separate
frontend build/deploy step.

Run from the repo root:
    uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000/
"""
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))  # allow `import sentinel` etc. when run as a package

from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import audit
import auth
import exodus
import graph_data
import intake
import sentinel
import weather as weather_mod
from ratelimit import RateLimitMiddleware

logger = logging.getLogger("agnimarg")

app = FastAPI(title="AGNIMARG Prototype API")
app.add_middleware(RateLimitMiddleware)

# Fine for this demo (falls back to a fixed, publicly-known key) — but a real
# deployment must set these, or every payload signature / session token is
# forgeable by anyone who reads this open-source repo. Warn loudly rather
# than fail silently into an insecure default.
if sentinel.USING_DEFAULT_SIGNING_KEY:
    logger.warning("AGNIMARG_SIGNING_KEY is not set — using the public demo default. Do not use this outside a local demo.")
if auth.USING_DEFAULT_AUTH_SECRET:
    logger.warning("AGNIMARG_AUTH_SECRET is not set — using the public demo default. Do not use this outside a local demo.")

_ROAD_GRAPH = graph_data.load_graph()
_EVENT = graph_data.load_hotspot_event()
_VILLAGE_NODE = graph_data.nearest_node(_ROAD_GRAPH, _EVENT["village_at_risk"]["lat"], _EVENT["village_at_risk"]["lon"])
_SHELTER_NODE = graph_data.nearest_node(_ROAD_GRAPH, _EVENT["shelter"]["lat"], _EVENT["shelter"]["lon"])

# Holds the most recent signed threat-cone payload + result, so the tamper-demo
# and dispatch-approval endpoints can act on "the last simulation" without the
# frontend having to round-trip the whole payload back to the server.
_LAST_SIM: dict = {}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    """Basic liveness/readiness check — matches the master blueprint's Phase 0
    DoD ('Flask returns {status: ok} on /'), adapted since our root path
    serves the frontend instead."""
    return {
        "status": "ok",
        "graph_nodes": _ROAD_GRAPH.number_of_nodes(),
        "graph_edges": _ROAD_GRAPH.number_of_edges(),
        "event_label": _EVENT["label"],
    }


def _require_auth(authorization: str | None) -> dict:
    """Extracts and verifies the Bearer token, returning {username, role}.
    Raises 401 if missing/invalid/expired — role is derived from the signed
    token here, never from anything the client claims in the request body."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = authorization.removeprefix("Bearer ")
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return payload


@app.post("/api/login")
def login(req: LoginRequest):
    user = auth.verify_credentials(req.username, req.password)
    if not user:
        audit.record("login_failed", actor=req.username, details={})
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = auth.issue_token(user["username"], user["role"])
    audit.record("login_succeeded", actor=user["username"], details={"role": user["role"]})
    return {"token": token, "username": user["username"], "role": user["role"]}


@app.get("/api/state")
def get_state():
    graph_edges = [
        [[_ROAD_GRAPH.nodes[u]["lat"], _ROAD_GRAPH.nodes[u]["lon"]],
         [_ROAD_GRAPH.nodes[v]["lat"], _ROAD_GRAPH.nodes[v]["lon"]]]
        for u, v in _ROAD_GRAPH.edges()
    ]
    return {
        "event_label": _EVENT["label"],
        "event_note": _EVENT["note"],
        "hotspots": _EVENT["hotspots"],
        "village_at_risk": _EVENT["village_at_risk"],
        "shelter": _EVENT["shelter"],
        "graph_edges": graph_edges,
        "graph_bbox": {"south": 29.32, "west": 79.40, "north": 29.44, "east": 79.52},
    }


@app.get("/api/weather")
def get_weather(mode: Literal["scenario", "live"] = "scenario"):
    if mode == "scenario":
        return _EVENT["fire_season_scenario_weather"]
    centroid_lat = sum(h["lat"] for h in _EVENT["hotspots"]) / len(_EVENT["hotspots"])
    centroid_lon = sum(h["lon"] for h in _EVENT["hotspots"]) / len(_EVENT["hotspots"])
    return weather_mod.fetch_live_weather(centroid_lat, centroid_lon)


@app.post("/api/simulate")
def simulate(mode: Literal["scenario", "live"] = "scenario"):
    if mode == "scenario":
        active_weather = _EVENT["fire_season_scenario_weather"]
    else:
        centroid_lat = sum(h["lat"] for h in _EVENT["hotspots"]) / len(_EVENT["hotspots"])
        centroid_lon = sum(h["lon"] for h in _EVENT["hotspots"]) / len(_EVENT["hotspots"])
        active_weather = weather_mod.fetch_live_weather(centroid_lat, centroid_lon)

    corroboration = intake.corroborate(_EVENT["hotspots"])
    audit.record("hotspots_corroborated", actor="INTAKE", details={
        "confirmed": len(corroboration["confirmed"]), "unconfirmed": len(corroboration["unconfirmed"]),
        "cluster_count": corroboration["cluster_count"],
    })

    signed = sentinel.build_signed_threat_payload(corroboration["confirmed"], active_weather)
    audit.record("threat_cone_generated", actor="SENTINEL", details={
        "risk_score": signed["payload"]["risk_score"], "signature": signed["signature"][:16] + "...",
    })

    try:
        result = exodus.process_signed_threat(_ROAD_GRAPH, signed, _VILLAGE_NODE, _SHELTER_NODE)
    except exodus.SignatureRejected as e:
        audit.record("threat_cone_rejected", actor="EXODUS", details={"reason": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

    audit.record("route_computed", actor="EXODUS", details={
        "rerouted": result["rerouted"], "blocked_edges": result["blocked_edge_count"],
        "safe_eta_min": result["safe_route"]["eta_min"],
    })

    global _LAST_SIM
    _LAST_SIM = {"signed": signed, "result": result, "generated_at": time.time()}

    return {
        "weather": active_weather,
        "risk_score": signed["payload"]["risk_score"],
        "signature": signed["signature"],
        "cones_by_hotspot": signed["payload"]["cones_by_hotspot"],
        "baseline_route": result["baseline_route"],
        "safe_route": result["safe_route"],
        "blocked_edge_count": result["blocked_edge_count"],
        "rerouted": result["rerouted"],
        "confirmed_hotspot_count": len(corroboration["confirmed"]),
        "unconfirmed_hotspots": corroboration["unconfirmed"],
    }


@app.post("/api/tamper-demo")
def tamper_demo():
    """Deliberately corrupts the last signed payload and replays it through EXODUS
    to prove Tier-1 audit finding #1 (no integrity check on the threat-cone
    payload) is actually fixed — EXODUS must reject it."""
    if not _LAST_SIM:
        raise HTTPException(status_code=400, detail="Run /api/simulate first.")

    tampered = {
        "payload": {**_LAST_SIM["signed"]["payload"], "risk_score": 0.99},  # mutate after signing
        "signature": _LAST_SIM["signed"]["signature"],  # stale signature, now invalid
    }
    try:
        exodus.process_signed_threat(_ROAD_GRAPH, tampered, _VILLAGE_NODE, _SHELTER_NODE)
        audit.record("tamper_demo", actor="EXODUS", details={"result": "ACCEPTED (unexpected!)"})
        return {"rejected": False}
    except exodus.SignatureRejected as e:
        audit.record("tamper_demo", actor="EXODUS", details={"result": "REJECTED", "reason": str(e)})
        return {"rejected": True, "reason": str(e)}


@app.post("/api/dispatch/approve")
def approve_dispatch(authorization: str | None = Header(default=None)):
    """Human-in-the-loop approval gate — Tier-1 audit finding #2. Role comes
    from the server-verified session token (see _require_auth), not from
    anything the client asserts — closes the earlier version of this demo
    where any client could just claim role="authority" in the request body."""
    identity = _require_auth(authorization)
    if identity["role"] != "authority":
        audit.record("dispatch_denied", actor=identity["username"], details={"reason": "insufficient role", "role": identity["role"]})
        raise HTTPException(status_code=403, detail="Only an authority-role user can approve dispatch.")
    if not _LAST_SIM:
        raise HTTPException(status_code=400, detail="Run /api/simulate first.")

    audit.record("dispatch_approved", actor=identity["username"], details={
        "safe_route_eta_min": _LAST_SIM["result"]["safe_route"]["eta_min"],
    })
    return {"approved": True, "message": "Dispatch approved. SMS alert simulated (see audit log) — no real SMS sent."}


@app.get("/api/audit-log")
def get_audit_log():
    return {"entries": audit.all_entries()}


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True), name="frontend")
