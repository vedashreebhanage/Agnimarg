# RESEARCH.md: Agnimarg research log

Convention: statements are from the source unless tagged [mine] (my own arithmetic or inference).
Entry format: Title/link/year | Problem | Data used | Method/algorithm | Tech stack | Results | Verified? | Gaps | Relevance
Log created: 2026-11-04. Status: E1-E7 approved by user; E8 pending identification.
User-selected focus for deeper work: E1 (Di Giuseppe), Indian-case-study papers (from E4/E5), E7 (NYU digital twin).

---

## E1. Global data-driven prediction of fire activity (Di Giuseppe, McNorton, Lombardi, Wetterhall), Nature Communications 16:2918, 2025
Link: https://doi.org/10.1038/s41467-025-58097-7 (open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC11962136/)
- Problem: Fire danger indices (FWI) predict dangerous weather, not actual fire. Can ML predict fire activity, and is data quality or model complexity the bottleneck?
- Data used: 19 predictors, 9 km, daily. Weather: ERA5-Land (T, dewpoint, wind, precipitation). Fuel: physical fuel model (live/dead load, moisture) + SMOS vegetation optical depth + LAI. Ignition: lightning, population density, road density, urban fraction, orography, vegetation type. Target: MODIS active fire (MCD14ML C6.1, low-confidence removed).
- Method/algorithm: XGBoost (operational), random forest (50 trees, depth 5), MLP (32,16 nodes); ablations over weather/fuel/ignition combinations. Cases: Canada 2023, Los Angeles 2025.
- Tech stack: XGBoost, ECMWF PoF system; data on Copernicus CDS; code DOI 10.24433/CO.8570224.v1; figure data on Zenodo.
- Results: Mid-complexity XGBoost matches/beats MLP; fuel is the most important single input; skill drops ~30% with weather-only or ignition-only. Text says 15% for fuel-only but Fig. 1 caption says 150%; text says 3-7% for two sources but caption says 17-13%.
- Verified?: Partly. Strengths: ablation design, probabilistic metrics (Brier, log loss, ECE, reliability), public peer-review file, open data/code.
- Gaps: Train/test split not described in the text read (supplement not read). Compares against FWI, a different quantity (Reviewer 1 noted). Averages skill across heterogeneous metrics. Target is 1 km active fire detections, not spread/perimeter. No India-specific result in main text.
- Relevance: High for ignition/risk layer and for ablation/calibration design.

## E2. From forecast skill to economic value: sub-hourly wildfire potential forecasting across Australian regions (Ardid et al.), Int. J. Wildland Fire 35, WF25221, 2026
Link: https://doi.org/10.1071/WF25221
- Problem: Daily danger ratings are too coarse. Can sub-hourly ML fire-potential forecasts beat the Fire Behaviour Index (FBI), and what are they worth in dollars?
- Data used: 9 weather stations, 3 Australian regions (Sunshine Coast, Brisbane, Hobart), 30-min data: T, RH, wind, dew point, pressure, rain; derived VPD, FFMC. 126 documented fires (15, 32, 79).
- Method/algorithm: 700+ tsfresh features over 10-day windows; 300-tree ensemble on ~1:2 under-sampled data; leave-one-fire-out and leave-region-out CV; Murphy cost-loss PEV (C = A$50k, L = A$10M).
- Tech stack: scikit-learn, tsfresh, Python 3.10; Zenodo 10.5281/zenodo.15692845.
- Results: AUC 0.88 vs 0.80 (Hobart), 0.89 vs 0.81 (Brisbane), 0.95 vs 0.73 (Sunshine Coast). Net savings 2.8x (Sunshine Coast) and 2.1x (Hobart) the FBI's, but only 1.03x at Brisbane.
- Verified?: Partly. CV design is the most leakage-aware of the set. Problems: [mine] net savings = PEV x A$150M for all tailored/FBI rows (e.g. 75.4/0.502 = 150.2; 63.2/0.421 = 150.1; 97.7/0.651 = 150.1), equal to L x 15 fires although Hobart has 79 and Brisbane 32 fires, contradicting the paper's Eqn 2; generalised rows do not follow this. Figures disagree with Table 1 (Fig 4 Brisbane ML 0.51/A$77M vs table 0.421/A$63.2M; Fig 5 FBI 0.20/A$30M vs table 0.23/A$34.5M; Fig 3 caption mixes threshold and PEV). Optimal threshold chosen retrospectively on test results. FBI recomputed from station data, not the official product. Abstract's "doubling savings" does not hold for Brisbane. Licence stated as MIT but commercial use prohibited without permission: check before reuse.
- Gaps: Point ignition potential, not spread or satellite imagery. Learning curve for one station only. "~30 fires suffice" limited to authors' own record.
- Relevance: Medium. PEV framing and leave-one-event-out protocol are the useful parts.

## E3. Geospatial system for wildfire monitoring and prediction using aerospace data (Moldamurat, La Spada, Bakyt), Natural Hazards Research 6, 516-533, 2026
Link: https://doi.org/10.1016/j.nhres.2025.12.002
- Problem: End-to-end early warning: ML detection, then cellular-automata (CA) spread, then calibrated probabilities and uncertainty bands (P50/P80/P95).
- Data used: Sentinel-2 and Landsat 8/9 at 20 m (NDVI, dNBR), VIIRS 375 m hotspots, SRTM, fuel maps, ERA5-Land and mesonet winds, UAV (validation only). 22 events (2019-2024): Kazakhstan, Portugal, Spain, California.
- Method/algorithm: Fully convolutional encoder-decoder CNN on 1024x1024 tiles with FRP head; CA seeded by detections, FRP-modulated (alpha = 0.35), re-anchored to new observations; 32-member ensemble (wind sigma = 1.5 m/s, alpha perturbation); isotonic-regression calibration.
- Tech stack: Linux GPU server, containers, Python 3.11, PyTorch 2.2, CUDA 12.1, GDAL 3.6, Rasterio 1.3, scikit-learn 1.5; proposed PostgreSQL/PostGIS, Leaflet/OpenLayers, REST API.
- Results (from paper): F1 97.1%, IoU 0.84 +/- 0.02 at 24 h (physics baseline 0.79, ML-only 0.75), arrival-time MAE 21 +/- 3 min, Brier 0.14, ECE 0.028, median latency ~300 min.
- Verified?: No. [mine] Fig 6 confusion matrix gives accuracy 99.05% vs 98.0% stated. Fig 7b at chosen threshold shows precision ~0.7, recall ~0.38 (read from plot) vs Table 2's 97.5% / 96.8%. Fig 6d claims AUC = 1.00. Pooled mAP 0.908 (Fig 8) vs micro-average AP 0.88 (Fig 7). Fig 2 lists events outside the four stated regions; Fig 1 includes 2018 events outside the stated period. Calibration set described inconsistently (validation vs disjoint calibration). On-time issuance ~95% in text vs 0.98 in Fig 11. Observation-update interval of 5 min cannot apply to Sentinel-2/Landsat scenes; Fig 1 shows ~2-3 usable S2 scenes in the 10 days before t0. FRP label source not stated. Only ~6-9 test events yet "statistically significant". Fig 6/9 maps look schematic and are not labelled synthetic [mine]. [mine, low confidence] No Brier skill score vs climatology; from Fig 5's prevalence line a constant forecast may score about 0.09-0.14, similar to reported 0.14-0.17. No code released. Several off-topic citations (BIM/IoT in construction, cotton biomass, human mobility and health, Global Carbon Budget).
- Gaps: Optical-only 6-hour updates unrealistic under cloud/smoke. No spotting or pyro-convection (authors admit). No evacuation component.
- Relevance: Highest topical fit (detection + spread + uncertainty + latency), numbers unverified.

## E4. Machine Learning and Deep Learning for Wildfire Prediction: Systematic and Bibliometric Review, 2020-2025 (Galvan Lara et al.), Fire 9, 204, 2026 (review)
Link: https://doi.org/10.3390/fire9050204
- Problem: Map algorithms, data practices, metrics and code availability in ML/DL wildfire prediction (PRISMA-EcoEvo, OSF-registered; 341 studies, detailed subset of 110).
- Data used: Scopus (1432) + Web of Science (321), English only, 2020-2025; query requires "decision making/decision support".
- Method/algorithm: Taxonomy of 9 algorithm families; descriptive statistics; chi-square on code availability.
- Tech stack: Python 3.11.12 (Colab), GeoPandas, Matplotlib; code on GitHub/Zenodo.
- Results (as reported): Tree ensembles 26.7%, deep learning 59.4%, vegetation/fuel inputs 44.7%, socioeconomic 1.2%, code shared 7.7%. Occurrence/risk 75.7% of studies, spread 1.5%.
- Verified?: Weak. [mine] 1730 - 1391 = 339, not 341. Yearly counts (2,5,20,24,33,57) sum to 141, not 341; "110 from 2024" cannot come from a 2024 count of 33. Reported percentages fit denominators 86, 85, 60 exactly, not 110 (e.g. 26.7% = 23/86; 44.7% = 38/85); 7.7% is not a whole fraction of 110. Chi-square df = 44 implies ~45 individual algorithms, not 9 families, and expected cell counts are far below 5 (invalid). Search string biases corpus. Off-topic citations (refs 22, 43).
- Gaps: Numbers unreliable; no quality appraisal of included studies.
- Relevance: Landscape and metric-hygiene lessons only. Do not cite its numbers.

## E5. Global review of wildfire prediction using spatio artificial intelligence models (Sinha & Sharma), Discover Forests 2:37, 2026 (review)
Link: https://doi.org/10.1007/s44415-026-00083-y
- Problem: Review of AI for wildfire susceptibility and prediction; 143 Web of Science papers (2000-2023). Authors at Central University of Rajasthan, India.
- Data used: Web of Science only.
- Method/algorithm: Systematic review with tabulation by algorithm, region, metrics; identifies gaps.
- Tech stack: n/a.
- Results (as reported): RF most used (20%), SVM 14%, ANN 12%. Evaluation relies on accuracy/AUC; calibration, uncertainty, spatial CV and transferability rarely done. Recommends spatio-temporal CV, MCC/TSS, calibration reporting.
- Verified?: Mostly weak. PRISMA arithmetic works (985 - 442 - 327 - 73 = 143), but [mine] Fig 8b yearly counts sum to 161, not 143; China is "23" in text, "25" in Fig 8c, 16% in text (25/143 = 17.5%); text says RF then ANN then ensembles but pie shows SVM 14% and ensembles 5%. Single database, no quality appraisal. Cross-study accuracy comparison invalid (authors concede). Mostly susceptibility (static), not forecasting.
- Gaps: As above.
- Relevance: Source of Indian case-study leads (Sikkim, Western Ghats, Western Himalayas, Uttarakhand, Eastern Ghats). Those papers not yet read.

## E6. Wildfire Emergency Response and Evacuation Framework Using Drones: Phase I (Kulhandjian), Mineta Transportation Institute, Oct 2025 (abstract only)
Link: https://transweb.sjsu.edu/research/2446-Wildfire-Emergency-Response-and-Evacuation
- Problem: Drone-based detection, evacuation planning and search-and-rescue.
- Data used: Not stated in abstract.
- Method/algorithm: "Dynamic Wildfire Response Algorithm" (DWRA): reinforcement learning, genetic algorithms, deep learning.
- Tech stack: IR and visible cameras, LiDAR, weather sensors, NVIDIA Jetson AGX Orin edge hardware.
- Results (abstract claims): 5x faster detection, 28% faster evacuation, 35% higher SAR efficiency. Baselines and test conditions not stated.
- Verified?: No. Full report not read (too large to fetch).
- Gaps: Unknown until full report read.
- Relevance: Only evacuation-specific source so far; prototype.

## E7. A New Physics-informed AI Tool Aims to Predict Wildfire Spread in Real Time (NYU Tandon, Panindre, Nair, Kumar), press release, 2026-10-28
Link: https://engineering.nyu.edu/news/new-physics-informed-ai-tool-aims-predict-wildfire-spread-real-time-and-assist-wildfire
(The phys.org URL provided could not be fetched; matched to this release by title/date only, not confirmed.)
- Problem: Real-time fire-spread forecasting with explainable output for incident commanders.
- Data used: Satellites, weather feeds, terrain, fuel, WUI, structures, drones, ground sensors.
- Method/algorithm: "Digital twin": physics-informed fire-spread model + AI layer solving equations of propagation, combustion, heat transfer, fuel, wind, slope; chat interface for strategy and evacuation advice. Not trained on historical fire data per the authors.
- Tech stack: Not stated. Provisional US patent filed.
- Results (press release): 3 US fires (Grasshopper OR, Widemouth 2 UT, Sacaton NM). 94.6% overlap on one Grasshopper forecast, down to 72.4% with a longer satellite gap; horizon up to 12 h; the figure example was a forecast ~3 h before the observed perimeter.
- Verified?: No. No paper found; overlap metric unspecified; no baseline; best of three fires highlighted; evacuation chatbot unvalidated.
- Gaps: Everything beyond the press release.
- Relevance: Low until a paper appears. Physics-plus-AI idea worth tracking; user is interested in including this direction later.

## E8. ScienceDirect link (S0301479723006965)
Unidentified. DOI believed to be 10.1016/j.jenvman.2023.117908 (J. Environ. Manage. 341), from other papers' reference lists. Title and authors not confirmed. No analysis until the paper is read.
