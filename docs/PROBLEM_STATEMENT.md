# PROBLEM_STATEMENT.md: Agnimarg

Stage 2 output. Written 2026-11-09. Scope approved by Ayush in conversation on 2026-11-07/09.
Companion files: docs/research/RESEARCH.md, docs/research/INDIA_PROBLEM.md,
docs/research/STAGE1_FINDINGS.md.

Conventions: unmarked statements are sourced (see the companion files for citations).
[mine] = Claude's inference. [UNVERIFIED] = secondary source only, primary not read.

---

## 1. The problem

India's forest fire response is detection-driven and reactive. The national system — the Forest
Survey of India's Forest Fire Alert System (FAST 3.0) — tells forest officers where a satellite
saw a thermal anomaly at the last overpass. It does not say where the fire will be in six hours,
which villages lie in its path, or how much time those people have.

Three gaps follow.

1. **Detection gap.** Satellite products miss most small fires in India: reportedly ~5.6% of
   Uttarakhand fire incidents detected by MODIS/VIIRS [UNVERIFIED], and under 20% of burned area
   in central India. Fires are found late, when they are already large.
2. **Prediction gap.** Indian wildfire research is almost entirely static susceptibility mapping.
   Spread forecasting is ~1.5% of the ML wildfire literature reviewed, and no validated
   India-specific spread model was found.
3. **Response gap.** No documented forest-fire evacuation system exists for India, despite
   12 deaths in Uttarakhand's 2024 season and dense village settlement inside fire-prone forest.

### Scale (ISFR 2023 / FSI)
- 27.97% of India's forest cover and scrub is extremely-to-highly fire prone.
- 2023-24 season: Uttarakhand had the most satellite detections (21,033); Andhra Pradesh had the
  largest estimated fire-affected area (5,286.76 sq km).
- Fire season: November–June, peak February–May.
- Most fires are human-caused (strongest evidence: an 83.4% drop in Western Himalayan fires during
  the 2020 COVID lockdown).

---

## 2. Who it is for

| User | What they need from Agnimarg | Interface |
|------|------------------------------|-----------|
| **Forest department staff** (primary) | Where fire risk is high today; where a fire is now; where it will move; where to send crews | Web dashboard |
| **District administration** (primary) | Which settlements are exposed; how much time they have; evacuation support | Web dashboard |
| **Villagers / community groups** (Van Panchayats, Mahila Mangal Dals) | Simple local warnings | Warning channel only (format to be decided in stage 3) |

Decided: users 1 and 2 are the product's users; villagers receive warnings but do not operate the system.

---

## 3. The solution

**Agnimarg: a spread-aware wildfire risk, prediction and evacuation-support platform for India.**

Software only for now. A ground-sensor pilot is deferred until the team meets.

### 3.1 Layers and build order

| # | Layer | What it does | Gate before starting |
|---|-------|--------------|----------------------|
| 1 | **Risk** | Daily fire probability per grid cell from weather, terrain, vegetation/fuel proxies and human factors | None — build first |
| 2 | **Detection** | Ingest satellite hotspots (VIIRS/MODIS) and track active fires | None — build alongside layer 1 |
| 3 | **Spread** | Where an active fire moves over the next 6–24 hours | Fuel-data check (section 5) |
| 4 | **Exposure** | Which villages and roads are in the predicted path; time to impact | Layer 3 producing output |
| 5 | **Evacuation routing** | Routes and timing for exposed settlements | Layer 3 validated against real fires; road-data coverage checked |
| 6 | **Digital twin** | Continuous live updating of an active fire's state from new observations | Layer 3 working |

Decided in stage 2:
- **Digital twin vs ML only:** ML first; digital twin is a later layer (6), not the starting point.
- **Spread prediction:** in scope, built after risk (layer 3).
- **Evacuation:** in scope as full evacuation planning, delivered in two steps — exposure and
  time-to-impact first (layer 4), routing once the spread model is validated (layer 5).

### 3.2 Design commitments (from the stage-1 research)
1. **Gradient-boosted trees** (XGBoost/LightGBM) for tabular risk prediction; neural networks only
   where the input is imagery or a space-time sequence. Evidence: on identical inputs XGBoost
   matched or beat a neural network (Di Giuseppe et al., Nature Communications 2025).
2. **Validation split by region and by year, never randomly.** Neighbouring pixels are correlated,
   so random splits inflate scores.
3. **Report calibration** (reliability curve, Brier score, expected calibration error), not only AUC.
   Fires are rare, so AUC alone misleads.
4. **Never train a small-fire model on satellite hotspots alone** — it would inherit the blind spot
   the project exists to fix. Use Sentinel-2 burn scars and/or field records as additional labels.
5. **Mask agricultural and industrial burning** out of hotspot labels.
6. **Clear disclaimer on evacuation outputs.** NASA's FIRMS terms advise against using its data
   for local tactical decisions; evacuation support must be validated and caveated.

---

## 4. Data availability (checked 2026-11-09)

Licences were read from source pages. Nothing has been downloaded yet.

| Need | Dataset | Licence | Access | Status |
|------|---------|---------|--------|--------|
| Fire labels | NASA FIRMS (VIIRS 375 m, MODIS 1 km) | NASA open data, "as is"; not advised for local tactical decisions | Free MAP_KEY by email; 5,000 transactions / 10 min | Usable |
| Fire spread history | Global Fire Atlas 2003–2016 (size, duration, speed, direction) | Not stated on landing page | NASA ORNL DAAC | Licence unclear; ends 2016 |
| Indian fire points | FSI Fire Point Search | No terms published | Web tool only; data from 01-11-2025 | No bulk download |
| Weather | ERA5-Land (9 km) | CC-BY 4.0 | Free Copernicus CDS account + API key | Usable |
| Weather (India) | IMD gridded (rain 0.25° since 1901; temperature 1° since 1951) | Not stated | `imdlib` Python package | Licence unclear; temperature grid coarse |
| Terrain | Copernicus DEM GLO-30 | Free; attribution wording mandatory | AWS, no login | Usable; confirm India tiles released (`tileList.txt`) |
| Land cover | ESA WorldCover 10 m (2020, 2021) | CC-BY 4.0 | AWS, no login | Usable |
| Vegetation / burn scars | Sentinel-2 L2A (10–20 m) | Free and open (Copernicus terms) | AWS, no login; STAC API | Usable, per event |
| Fuel (India) | FSI "Surface Fuel Load Mapping 2023-24" (TIS Vol 3 No 2, 2026) | Report | PDF on FSI site | Exists; raster not public |
| Fuel (global) | ECMWF fuel characteristic dataset (9 km daily) | CC-BY 4.0 (paper) | Hosting not yet located | Locate |
| Population | WorldPop India 100 m, 2020 (constrained) | CC-BY 4.0 | Direct download | Usable |
| Roads / settlements | OpenStreetMap (Geofabrik India extract) | ODbL (share-alike) | Direct download | Usable; rural hill coverage unmeasured |
| Village boundaries | SHRUG / Development Data Lab (Census 2011) | Open-access; licence not named | Contact DDL | Licence unclear |
| Land use (India) | Bhuvan (NRSC/ISRO) | Single-user licence; no internet hosting of originals | Registration | Avoid for a public product |

---

## 5. Known risks and dependencies

| Risk | Affects | Mitigation / next check |
|------|---------|-------------------------|
| No downloadable Indian fuel raster | Layers 3, 5, 6 | Request FSI's 2023-24 surface fuel load data; fall back to ECMWF global fuel dataset + WorldCover + NDVI proxies |
| Satellite labels miss small fires | Layers 1–3 | Sentinel-2 burn-scar labels; forest-department records where obtainable |
| Official data conflicts (~150x for Uttarakhand 2023-24 area) | Validation | Understand each source's definition before using it as ground truth |
| Road coverage in hill villages unknown | Layer 5 | Measure OSM completeness in the pilot region before building routing |
| Evacuation errors can cost lives | Layer 5 | Gate on validated spread model; decision support with disclaimers, not automated orders |
| Licences unclear (Global Fire Atlas, IMD, SHRUG) | Several | Confirm before any public deployment |

---

## 6. Open decisions

1. **Pilot region.** Proposed: Uttarakhand (most 2023-24 detections, 12 deaths in 2024, villages
   inside forest, steep terrain). Alternative: Odisha (largest burnt areas). Not yet decided.
2. **Village warning channel** (SMS, WhatsApp, IVR or other) — stage 3.
3. **Whether to request FSI's fuel raster** — draft email offered, not yet sent.
4. **Data storage location** — a folder on Ayush's PC or in the repository (large rasters should not
   go into git).

---

## 7. Next stages (Ayush's plan)
3. Feasibility analysis; innovate on overcoming the challenges.
4. Extract all datasets (pilot region first).
5. Model document: how we train, which model, advantages/disadvantages, how it helps.
6. Repository build-out.
