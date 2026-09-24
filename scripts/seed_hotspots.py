"""
Writes backend/data/hotspots.json — the seeded demo fire event.

This is NOT a live NASA FIRMS pull (that needs a free personal MAP_KEY — see
fetch_data.py's docstring). Instead it replays a fire in the same forest belt
around Pangot/Kilbary, near Nainital, Uttarakhand — an area that has recurring
pine-forest fire activity during the Apr-Jun fire season, most notably 2021,
which was one of India's worst recent forest-fire years in this belt.

The exact coordinates/timestamps below are illustrative placements for the demo,
not a reproduction of a specific FIRMS archive record — the UI must label this as
"seeded / demo data", never as a live feed. Swap in a real FIRMS MAP_KEY pull
later to replace this file with true satellite hotspots.

Run: python scripts/seed_hotspots.py
"""
import json
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "data")

HOTSPOTS = [
    {
        "id": "seed-1",
        "lat": 29.4187,
        "lon": 79.4310,
        "confidence": "nominal",
        "frp_mw": 18.4,
        "near": "Pangot forest belt",
    },
    {
        "id": "seed-2",
        "lat": 29.4201,
        "lon": 79.4338,
        "confidence": "high",
        "frp_mw": 27.1,
        "near": "Pangot forest belt",
    },
    {
        "id": "seed-3",
        "lat": 29.4172,
        "lon": 79.4295,
        "confidence": "nominal",
        "frp_mw": 12.9,
        "near": "Kilbary ridge",
    },
]

VILLAGE_AT_RISK = {"name": "Pangot", "lat": 29.42413, "lon": 79.4270401}
SHELTER = {"name": "Sitapur Hospital, Nainital", "lat": 29.3905118, "lon": 79.457564}

# Representative April-June fire-season conditions for this belt (hot, dry,
# moderate wind) — NOT live data. Live September weather here is off-season
# (monsoon-damp) and would make the risk score near zero, which defeats the
# point of a demo. Wind direction is set toward the village->shelter bearing
# (141.6 deg) so the seeded scenario plausibly threatens the real evacuation
# corridor, same as a real fire pushed by a prevailing wind would.
FIRE_SEASON_SCENARIO_WEATHER = {
    "source": "seeded fire-season scenario (Apr-Jun representative, NOT live)",
    "temperature_c": 34.0,
    "humidity_pct": 15.0,
    "wind_speed_kmh": 20.0,
    "wind_direction_deg": 322,  # wind FROM the NW, pushing plume toward the SSE corridor
    "observed_at": None,
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "label": "SEEDED DEMO EVENT — not a live FIRMS feed",
        "note": (
            "Illustrative fire event in the Pangot/Kilbary forest belt near Nainital, "
            "Uttarakhand, replayed as 'now' for demo reliability. This region has real "
            "recurring pine-forest fire activity in the Apr-Jun season (2021 was severe). "
            "Add a NASA FIRMS MAP_KEY to replace this with a live satellite feed."
        ),
        "hotspots": HOTSPOTS,
        "village_at_risk": VILLAGE_AT_RISK,
        "shelter": SHELTER,
        "fire_season_scenario_weather": FIRE_SEASON_SCENARIO_WEATHER,
    }
    with open(os.path.join(OUT_DIR, "hotspots.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Wrote backend/data/hotspots.json")


if __name__ == "__main__":
    main()
