# AGNIMARG — Mid-Semester Review Build Plan (Software-Only Prototype)

**Status: built and working tonight.** This file records what exists, why it was scoped this way, and what's explicitly left for later — so the review reads as an intentional scope decision, not an unfinished project.

## Source documents (read in full before any code was written)

- `agnimarg-architecture-audit-space.html` — original 4-part architecture, team split, 15-point security audit
- `comparativeStudy.html` — global vs. India gap analysis; names EXODUS (dynamic evacuation routing) as the differentiator
- `agnimarg_master_blueprint.html` — full production blueprint: 14 phases, PostGIS, Celery, CesiumJS, XGBoost, YOLO. A multi-week/6-month build, not a one-night one — used here as the terminology/module reference (SENTINEL, EXODUS), not as tonight's task list.
- `Agnimarg_Complete_Software_Tech_Stack_India.pdf` — research-grade exact data-source stack (MOSDAC, Bhoonidhi, INSAT-3DS, etc.), mostly requiring institutional registration. Reference only.
- `AGNIMARG_Prototype_Plan.docx` — **the actionable document.** A ₹0, free-tier, 5-week roadmap for a 4-person team, with an explicit "what to mock/skip for prototype" list. Tonight's build compresses this further (5 weeks → 1 night, solo) but keeps its stack choices and its mocking philosophy.
- `AGNIMARG_Literature_Review.docx` — academic prior-art survey; used for the "novelty" framing in the review, not for implementation.

## Scope decision

Hardware/sensor track: dropped (budget, per your instruction). Full XGBoost/ConvLSTM/PostGIS/CesiumJS production stack: **not built tonight** — that's weeks of work per the project's own blueprint and explicitly flagged there as such. What's built is the software-only slice the Prototype Plan doc itself calls the "₹0 architecture," compressed to what one person can build and verify working in one night.

| Part | Tonight's build | Explicitly deferred (roadmap only) |
|---|---|---|
| INTAKE | Real OSM road network (Overpass API) + real place/hospital data for Nainital, Uttarakhand. Live Open-Meteo weather (no API key). Seeded historical-style fire event (Pangot/Kilbary forest belt) by default — **or live NASA FIRMS hotspots if you set `AGNIMARG_FIRMS_MAP_KEY`** (see `backend/firms.py`), with automatic fallback to seeded data if the key is missing or the request fails. Multi-source corroboration (`backend/intake.py`): hotspots are clustered (distance-based, mirrors the master blueprint's DBSCAN eps=1km/min_samples=2 spec) and only clusters of 2+ corroborating points feed SENTINEL — an isolated single-point report is flagged, not trusted. | PostGIS, Airflow/Celery ingestion |
| SENTINEL | FWI-style heuristic risk score (temp + humidity + wind — real live/scenario weather in, real number out) driving a real downwind threat-cone geometry (1h/3h/6h rings). HMAC-SHA256 signs every payload. | XGBoost ignition model, CNN-BiLSTM/ConvLSTM spread, MLflow versioning |
| EXODUS | Real NetworkX Dijkstra routing over the real OSM graph. Verifies the HMAC signature before acting — rejects tampered payloads live (demoed, not just claimed). Dynamically re-costs/blocks edges inside the threat cone and reroutes. | OSRM/GraphHopper, multi-modal transit, OR-based vehicle pre-positioning |
| INTERFACE | Single-page Leaflet dashboard: live map, cones, before/after routes, real username/password login with signed session tokens (`backend/auth.py`), human-approval dispatch gate, SQLite-persisted audit log. | Real OAuth2/OIDC (Google/etc.), real SMS (MSG91), Supabase/Postgres |

## Why the specific security controls built tonight

Per the original audit doc's Tier-1 findings — HMAC signing (finding #1) and the human-approval gate (finding #2) are the two cheapest-to-build, highest-impact controls, so they're real and demoable, not just described. Role comes from a server-verified signed session token (`backend/auth.py`), not a client-asserted field — an earlier version of this build trusted whatever role the client claimed in the request body, which meant anyone could call the API directly and skip the login UI; that gap is now closed and covered by a regression test (`tests/test_api.py::test_dispatch_approve_rejects_forged_role_in_body`). Password hashing (SHA-256) and demo credentials are intentionally minimal/public — matches the Prototype Plan's own "Authentication: Yes (basic)" bar, not a production auth system.

Also covers, cheaply: rate limiting (`backend/ratelimit.py`, Tier-2 requirement — stricter on `/api/login` to slow brute-forcing the weak demo passwords), dependency scanning (`.github/dependabot.yml`, Tier-3 finding — weekly automated PRs for pip + Actions), and a loud startup warning (not a silent fallback) if the HMAC signing key or auth secret is left at its public demo default (`backend/main.py`).

## Repo layout (built)

```
/backend
  main.py         FastAPI app: /api/login, /api/state, /api/weather, /api/simulate,
                   /api/tamper-demo, /api/dispatch/approve, /api/audit-log — also serves
                   /frontend as static files
  graph_data.py    Loads the OSM graph + seeded/live event data
  weather.py       Live Open-Meteo fetch (fails soft to a labeled fallback if offline)
  firms.py         Optional live NASA FIRMS hotspot pull (AGNIMARG_FIRMS_MAP_KEY)
  intake.py        Multi-source corroboration (distance clustering, flags isolated reports)
  ratelimit.py     Per-IP rate limiting middleware (stricter on /api/login)
  sentinel.py      Risk score + threat-cone geometry + HMAC sign/verify
  exodus.py        Point-in-polygon re-costing, Dijkstra routing, signature verification
  auth.py          Username/password login + signed session tokens (real, intentionally minimal)
  audit.py         SQLite-persisted audit log
  data/            road_graph.json, places.json, hotspots.json — generated, committed for
                   offline demo reliability. audit.db is gitignored runtime state.
/frontend
  index.html, style.css, app.js   Leaflet dashboard, no build step
/scripts
  fetch_data.py     Regenerates road_graph.json/places.json from live Overpass API
  seed_hotspots.py  Regenerates hotspots.json (seeded fire event + fire-season scenario weather)
/tests
  54 pytest cases covering sentinel/exodus/auth/firms/graph_data/weather/
  ratelimit/intake logic + the full HTTP API
```

## Run it

```
pip install fastapi uvicorn networkx requests
uvicorn backend.main:app --reload
```
Open `http://127.0.0.1:8000/`. Click **"Run simulation (fire-season scenario)"** — this is the reliable demo path (works with or without internet, since only the road/place data was pulled live and is now cached in `backend/data/`). **"Run with live weather instead"** hits Open-Meteo live and shows real current conditions for the region, at the cost of being weaker for a demo when the actual weather is calm (that's *why* the scenario mode exists — see `weather.py`/`seed_hotspots.py` docstrings for the honest reasoning).

## Demo script for the review

1. Show the map: real village (Pangot), real shelter (Sitapur Hospital, Nainital), seeded fire markers — point out the on-screen banner that honestly labels this as seeded, not live.
2. Click "Run simulation" — cones appear (live-computed geometry, not a static image), risk score and HMAC signature shown.
3. Point out the green safe route bending around the red/orange cone vs. the gray baseline route that ignores it — this is the EXODUS differentiator the comparative-study doc calls out.
4. Click "Tamper the signed payload & replay" — show EXODUS reject it. This directly answers Tier-1 audit finding #1 live, not on a slide.
5. Log in as `citizen1` / `demo-citizen-pass`, try "Approve dispatch" — denied (403). Log in as `authority1` / `demo-authority-pass`, approve — succeeds, logged under the real authenticated username. Answers Tier-1 finding #2.
6. Show the audit log — answers Tier-1 finding #4.
7. State plainly what's roadmap vs. built (the table above) — the Complete Software Tech Stack PDF and master blueprint are the "where this goes next" story, not tonight's claim.

## Honest limitations (say these out loud in the review, don't let them be found)

- Fire hotspots are seeded by default, not a live FIRMS feed — set `AGNIMARG_FIRMS_MAP_KEY` (free, instant: https://firms.modaps.eosdis.nasa.gov/api/map_key/) to go live; falls back to seeded data automatically if unset or the request fails.
- Risk score is an explicit FWI-style heuristic, not a trained ML model — same simplification the Prototype Plan doc itself recommends for the prototype stage.
- Audit log persists to SQLite (`backend/data/audit.db`, gitignored — runtime state, not build input) — fine for a demo/single-machine deployment, a real deployment would use managed Postgres.
- Auth is a hardcoded 2-user demo table with SHA-256-hashed passwords and HMAC-signed session tokens — real, but intentionally minimal (no real OAuth/DB-backed users), matching the Prototype Plan's "basic" bar.
- Offline fallback (`frontend/app.js`, Tier-1 audit finding #3) caches the last-good `/api/state` and `/api/simulate` responses in `localStorage` and falls back to them with a clear "OFFLINE — showing cached data" banner if a later request fails while the app is already open — verified in-browser: loaded the app, ran a simulation, killed the server, clicked "Run simulation" again, got the cached result with the offline banner instead of a bare error. This does **not** cover a cold page load while the server is down (the browser can't fetch `app.js` itself in that case, 503/connection error) — a true "app shell" offline load would need a service worker, which is out of scope tonight. Say this distinction out loud if asked: it degrades gracefully mid-session, not from a dead start.
- Routing graph covers one bounded region (Nainital) — proof of concept, not national coverage.
