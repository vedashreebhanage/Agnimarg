"""SENTINEL — the prediction slice of tonight's demo.

Per the project's own Prototype Plan doc: ignition/spread risk here is an
explicit FWI-style heuristic baseline (temperature + humidity + wind), not the
XGBoost/ConvLSTM models described in the full blueprint — those are documented
roadmap items, not built tonight. The threat "cone" is real geometry (a downwind
wedge sized by wind speed and risk, per hour horizon) built from real live wind
data, not a placeholder shape.

Every generated threat-cone payload is HMAC-signed before EXODUS is allowed to
act on it — the one Tier-1 security-audit control (see agnimarg-architecture-audit-
space.html) that is cheap enough to actually implement and demo tonight.
"""
import hashlib
import hmac
import json
import math
import os
import time

_DEFAULT_SIGNING_KEY = "demo-only-not-for-production-use"
SECRET_KEY = os.environ.get("AGNIMARG_SIGNING_KEY", _DEFAULT_SIGNING_KEY).encode()
USING_DEFAULT_SIGNING_KEY = SECRET_KEY == _DEFAULT_SIGNING_KEY.encode()

EARTH_RADIUS_KM = 6371.0
HORIZONS_HOURS = [1, 3, 6]


def compute_risk_score(temp_c: float, humidity_pct: float, wind_kmh: float) -> float:
    """Simplified FWI-style heuristic: hot + dry + windy -> higher ignition/spread risk.
    Bounded to [0, 1]. This is intentionally simple — a real deployment would use the
    project's planned XGBoost ignition model trained on ERA5-Land + fuel + terrain."""
    temp_term = max(0.0, min(1.0, (temp_c - 10) / 30))
    dryness_term = max(0.0, min(1.0, (100 - humidity_pct) / 100))
    wind_term = max(0.0, min(1.0, wind_kmh / 40))
    risk = 0.4 * temp_term + 0.4 * dryness_term + 0.2 * wind_term
    return round(max(0.0, min(1.0, risk)), 3)


def _destination_point(lat, lon, bearing_deg, distance_km):
    """Great-circle destination point given a start, bearing, and distance."""
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing_deg)
    d_r = distance_km / EARTH_RADIUS_KM

    lat2 = math.asin(math.sin(lat1) * math.cos(d_r) + math.cos(lat1) * math.sin(d_r) * math.cos(brng))
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d_r) * math.cos(lat1),
        math.cos(d_r) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def _wedge_polygon(center_lat, center_lon, downwind_bearing_deg, radius_km, half_angle_deg, arc_points=10):
    """Apex-at-source downwind wedge — approximates a probabilistic spread cone."""
    if radius_km <= 0:
        return [[center_lat, center_lon]]
    poly = [[center_lat, center_lon]]
    for i in range(arc_points + 1):
        frac = i / arc_points
        bearing = downwind_bearing_deg - half_angle_deg + frac * (2 * half_angle_deg)
        lat, lon = _destination_point(center_lat, center_lon, bearing, radius_km)
        poly.append([lat, lon])
    poly.append([center_lat, center_lon])
    return poly


def generate_threat_cones(hotspot: dict, wind_speed_kmh: float, wind_dir_from_deg: float, risk_score: float) -> dict:
    """Build 1h/3h/6h downwind threat-cone polygons for one hotspot.
    wind_dir_from_deg follows meteorological convention (direction wind blows FROM);
    the plume travels the opposite way, i.e. + 180 degrees."""
    downwind_bearing = (wind_dir_from_deg + 180) % 360
    # effective spread rate blends baseline fuel-driven creep with wind push,
    # scaled by risk score — same shape as the blueprint's wind-factor idea,
    # collapsed into one coefficient instead of a full cellular-automaton raster.
    base_spread_kmh = 0.15 + 0.6 * risk_score
    wind_push = 1 + (wind_speed_kmh / 30)
    spread_rate_kmh = base_spread_kmh * wind_push
    half_angle_deg = 32 - 12 * risk_score  # higher risk -> more directional/narrower plume

    cones = {}
    for hours in HORIZONS_HOURS:
        radius_km = spread_rate_kmh * hours
        cones[f"{hours}h"] = {
            "hours": hours,
            "radius_km": round(radius_km, 3),
            "polygon": _wedge_polygon(hotspot["lat"], hotspot["lon"], downwind_bearing, radius_km, half_angle_deg),
        }
    return cones


def build_signed_threat_payload(hotspots: list, weather: dict) -> dict:
    risk_score = compute_risk_score(weather["temperature_c"], weather["humidity_pct"], weather["wind_speed_kmh"])
    cones_by_hotspot = {
        h["id"]: generate_threat_cones(h, weather["wind_speed_kmh"], weather["wind_direction_deg"], risk_score)
        for h in hotspots
    }
    payload = {
        "generated_at": time.time(),
        "risk_score": risk_score,
        "weather": weather,
        "cones_by_hotspot": cones_by_hotspot,
    }
    signature = sign_payload(payload)
    return {"payload": payload, "signature": signature}


def sign_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest()


def verify_payload(payload: dict, signature: str) -> bool:
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)
