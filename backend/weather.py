"""Live weather via Open-Meteo — free, no API key, matches the Prototype Plan doc's
recommendation ("best free weather"). This is genuinely live data, not seeded."""
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_live_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
    }
    try:
        r = requests.get(OPEN_METEO_URL, params=params, timeout=8)
        r.raise_for_status()
        cur = r.json()["current"]
        return {
            "source": "open-meteo (live)",
            "temperature_c": cur["temperature_2m"],
            "humidity_pct": cur["relative_humidity_2m"],
            "wind_speed_kmh": cur["wind_speed_10m"],
            "wind_direction_deg": cur["wind_direction_10m"],
            "observed_at": cur["time"],
        }
    except requests.RequestException as e:
        # Fail soft with a clearly-labeled fallback so the demo survives a flaky
        # connection at review time, rather than the whole simulation erroring out.
        return {
            "source": "fallback (open-meteo unreachable)",
            "temperature_c": 28.0,
            "humidity_pct": 22.0,
            "wind_speed_kmh": 14.0,
            "wind_direction_deg": 250,
            "observed_at": None,
            "error": str(e),
        }
