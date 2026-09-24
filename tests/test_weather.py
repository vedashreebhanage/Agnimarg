import requests

import weather


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def test_fetch_live_weather_success(monkeypatch):
    fake_payload = {
        "current": {
            "temperature_2m": 22.5,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 8.0,
            "wind_direction_10m": 180,
            "time": "2026-04-15T12:00",
        }
    }
    monkeypatch.setattr(weather.requests, "get", lambda *a, **kw: _FakeResponse(fake_payload))

    result = weather.fetch_live_weather(29.4, 79.4)
    assert result["source"] == "open-meteo (live)"
    assert result["temperature_c"] == 22.5
    assert result["wind_speed_kmh"] == 8.0
    assert "error" not in result


def test_fetch_live_weather_fails_soft_on_network_error(monkeypatch):
    def raise_connection_error(*a, **kw):
        raise requests.ConnectionError("simulated network failure")

    monkeypatch.setattr(weather.requests, "get", raise_connection_error)

    result = weather.fetch_live_weather(29.4, 79.4)
    assert result["source"] == "fallback (open-meteo unreachable)"
    assert "error" in result
    # still returns usable numeric fields so callers don't have to special-case this
    assert isinstance(result["temperature_c"], float)


def test_fetch_live_weather_fails_soft_on_http_error(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda *a, **kw: _FakeResponse({}, status_code=500))
    result = weather.fetch_live_weather(29.4, 79.4)
    assert result["source"] == "fallback (open-meteo unreachable)"
