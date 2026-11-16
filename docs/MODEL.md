# MODEL.md: Agnimarg model decisions

Approved by Ayush on 2026-11-16.
[mine] = Claude's inference or estimate, not a measured or sourced fact.

---

## 1. What the software delivers

One website for forest department staff and district administration, run on localhost first and
hosted later, covering one region at a time.

| Part | In the software? | Method |
|------|------------------|--------|
| Fire history (past detections, burned areas, repeat-fire zones) | Yes | Maps from FIRMS and the Global Fire Atlas; no ML |
| Current detections | Yes | Live FIRMS feed, clustered with DBSCAN; no ML |
| Risk forecast with calibrated probabilities | Yes | LightGBM (section 3) |
| Ranked patrol list | Yes | Ranking of risk-forecast cells per district |
| Exposure | Yes | Villages and roads inside precautionary threat zones or high-risk cells |
| Evacuation routing | Yes | Shortest path avoiding threat zones (Dijkstra, as in the prototype) |
| Spread, as needed for evacuation | Yes, precautionary only | Worst-case threat zones (section 4) |
| Validated spread forecasting | Research only | Physics-based cellular automaton, later ML correction |

## 2. Regions

- Region 1: Uttarakhand. Decided 2026-11-16.
- Region 2: not chosen. To be added only after Uttarakhand works end to end, as a test of whether
  the method transfers. Candidate evidence (VIIRS S-NPP, Feb-Jun 2017-2026, type 0, nominal/high
  confidence, NOT forest-masked so crop burning is included): Madhya Pradesh 481,149 detections;
  Odisha 288,577; Maharashtra 269,065; Chhattisgarh 265,272; Uttarakhand 89,819.
- Each region is one configuration file, so adding a region does not change the code.

Reason for the narrow coverage: the development PC has 7.7 GB RAM, 2 processor cores, no dedicated
graphics card and about 15 GB free disk (measured 2026-11-16).

## 3. Risk model (proposed decisions)

| # | Decision | Choice |
|---|----------|--------|
| M1 | Prediction unit | 1 km cell x 1 day, forest and scrub cells only |
| M2 | Label | At least one VIIRS detection that day with type 0 and nominal/high confidence, after masking cropland and built-up cells with WorldCover |
| M3 | Model | LightGBM; XGBoost run once as a cross-check |
| M4 | Baselines to beat | Climatology (cell's historical fire rate for that month); the prototype's FWI-style heuristic; logistic regression |
| M5 | Split | Train on seasons to 2022, validate on 2023, test on 2024 onward. Also hold out a region: train Garhwal, test Kumaon, and the reverse |
| M6 | Imbalance | Keep all fire rows, sample no-fire rows, correct probabilities afterwards |
| M7 | Features | Weather (ERA5-Land daily values and rolling sums), terrain (elevation, slope, aspect), land cover, distance to roads and settlements, population, past fires (earlier dates only), day of year |
| M8 | Metrics | PR-AUC, Brier score, expected calibration error, reliability curve, cost-loss value |
| M9 | Reproducibility | Fixed seed, pinned library versions, each run records the manifest SHA-256 of its inputs |

Calibration: isotonic regression fitted on the validation season.

Leakage rule: every feature uses only data from before the prediction date. An automated test
checks this on every run.

### Quality bars before the forecast is shown as a product
1. Beats all three baselines on the held-out seasons and on the held-out region.
2. Probabilities are calibrated: cells given 10% see fire on about 10% of such days.
3. Same inputs always give the same map.
4. A late or broken data feed is reported on the map, never hidden.
5. Known limits are printed on the product.

### Known limits
- Labels are satellite detections, so the model predicts satellite-visible fires. Small fires and
  fires under cloud or canopy are under-represented. Sentinel-2 burn scars (6 events so far) are an
  independent check, not a fix.
- ERA5-Land weather is about 9 km; one weather cell can span a valley and a ridge.
- ERA5-Land is published about 5 days late. The live forecast needs a forecast weather source,
  not yet chosen; the model must be tested on that source before release.
- 2024 was a severe season in Uttarakhand, so test scores may not reflect a typical year. [mine]
- A deep-learning model on space-time grids may do better. It will be compared on the same split
  once the tree model works; this needs a graphics card (Google Colab).

## 4. Threat zones for exposure and evacuation

- From each active fire cluster, draw the area fire could plausibly reach in 1, 3 and 6 hours,
  stretched downwind and uphill.
- Spread rates are set deliberately high, from Global Fire Atlas speeds for Indian fires, checked
  against our Sentinel-2 burn scars. Values not yet derived.
- These are worst-case zones, not forecasts. They will often include villages the fire never
  reaches. The website must say so, and present evacuation output as decision support for
  officials, not an instruction to the public.
- This replaces the stage-2 gate "routing only after the spread model is validated", by Ayush's
  decision on 2026-11-16.

## 5. Burn-scar labels

dNBR (drop in Normalized Burn Ratio between pre-fire and post-fire Sentinel-2 scenes) with a
threshold, checked by eye for terrain shadow, snow melt and seasonal leaf drop. A U-Net is
considered only if thresholding fails.

## 6. Backend (proposals for the team)

| # | Decision | Choice |
|---|----------|--------|
| B1 | Where the model runs | Offline daily batch job writes a risk grid; FastAPI only serves it |
| B2 | Storage | Files (GeoTIFF, Parquet) while on localhost; PostGIS when hosted |
| B3 | SENTINEL heuristic | Kept as fallback and baseline until the ML forecast passes the quality bars |
| B4 | Model versioning | One folder per model version with a metadata file (data hashes, seed, versions, metrics) |
| B5 | Evacuation output | Labelled as precautionary decision support |

## 7. Not yet decided
- Forecast weather source for the live map.
- Fuel data: ECMWF fuel dataset (key saved, not yet downloaded); FSI raster (email not sent).
- Threat-zone spread rates.
- Second region.
- Map of forest divisions and ranges for patrol lists; districts are the fallback.
