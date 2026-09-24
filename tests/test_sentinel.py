import sentinel


def test_risk_score_bounds():
    # hot, dry, windy -> high risk
    hot_dry_windy = sentinel.compute_risk_score(temp_c=40, humidity_pct=5, wind_kmh=40)
    assert 0.9 <= hot_dry_windy <= 1.0

    # cold, humid, still -> low risk
    cold_wet_calm = sentinel.compute_risk_score(temp_c=5, humidity_pct=100, wind_kmh=0)
    assert 0.0 <= cold_wet_calm <= 0.1

    # always bounded regardless of extreme/out-of-range inputs
    extreme = sentinel.compute_risk_score(temp_c=200, humidity_pct=-50, wind_kmh=500)
    assert 0.0 <= extreme <= 1.0


def test_risk_score_monotonic_in_temperature():
    cooler = sentinel.compute_risk_score(temp_c=15, humidity_pct=50, wind_kmh=10)
    hotter = sentinel.compute_risk_score(temp_c=35, humidity_pct=50, wind_kmh=10)
    assert hotter > cooler


def test_sign_and_verify_roundtrip():
    payload = {"a": 1, "b": [1, 2, 3], "risk_score": 0.5}
    signature = sentinel.sign_payload(payload)
    assert sentinel.verify_payload(payload, signature) is True


def test_verify_rejects_tampered_payload():
    payload = {"risk_score": 0.5}
    signature = sentinel.sign_payload(payload)
    tampered = {"risk_score": 0.99}  # mutated after signing
    assert sentinel.verify_payload(tampered, signature) is False


def test_verify_rejects_wrong_signature():
    payload = {"risk_score": 0.5}
    assert sentinel.verify_payload(payload, "not-a-real-signature") is False


def test_threat_cone_radius_grows_with_horizon():
    hotspot = {"lat": 29.42, "lon": 79.43}
    cones = sentinel.generate_threat_cones(hotspot, wind_speed_kmh=20, wind_dir_from_deg=320, risk_score=0.7)
    assert cones["1h"]["radius_km"] < cones["3h"]["radius_km"] < cones["6h"]["radius_km"]


def test_threat_cone_apex_at_hotspot():
    hotspot = {"lat": 29.42, "lon": 79.43}
    cones = sentinel.generate_threat_cones(hotspot, wind_speed_kmh=20, wind_dir_from_deg=320, risk_score=0.7)
    apex = cones["6h"]["polygon"][0]
    assert apex == [hotspot["lat"], hotspot["lon"]]


def test_build_signed_threat_payload_end_to_end():
    hotspots = [{"id": "h1", "lat": 29.42, "lon": 79.43}]
    weather = {"temperature_c": 34, "humidity_pct": 15, "wind_speed_kmh": 20, "wind_direction_deg": 322}
    signed = sentinel.build_signed_threat_payload(hotspots, weather)
    assert sentinel.verify_payload(signed["payload"], signed["signature"]) is True
    assert "h1" in signed["payload"]["cones_by_hotspot"]
