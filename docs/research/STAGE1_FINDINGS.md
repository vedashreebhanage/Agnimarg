# STAGE1_FINDINGS.md: Agnimarg stage 1 — gaps, options and open questions

Drafted 2026-11-04. Not yet reviewed by Ayush.
Companion files: RESEARCH.md (paper analyses E1-E8), INDIA_PROBLEM.md (India problem brief).

Convention: [mine] = my inference, not a sourced finding. [UNVERIFIED] = secondary source only.
NOTHING IN THIS FILE IS A DECISION. Options are listed for stage 2 to choose from.

---

## 1. What stage 1 covered

Done:
- Six studies analysed and logged (RESEARCH.md E1-E7; E8 unidentified).
- India problem researched end to end (INDIA_PROBLEM.md): fire science, scale, causes,
  season, regions, existing systems, community response, evacuation, datasets.
- Gaps identified (section 3 below).
- Options for small-fire detection enumerated (section 4) — NOT chosen.
- ML vs deep learning question answered with evidence (section 5).

Not done:
- SJSU/Kulhandjian full report not read (PDF too large to fetch) — the only
  evacuation-specific source in the set.
- ScienceDirect paper (S0301479723006965) unidentified; DOI believed
  10.1016/j.jenvman.2023.117908 but title/authors unconfirmed.
- Dataset licences not verified for any source.
- Several primary sources behind key statistics not read (listed in section 7).

---

## 2. What the literature actually established

From RESEARCH.md, the findings that survived scrutiny:

1. Data quality beats model complexity. XGBoost matched or beat a neural network on the same
   inputs; adding fuel and ignition data helped far more than adding model depth
   (E1, Di Giuseppe et al. 2025). Note: the ML-comparison was added during peer review and the
   models were only lightly tuned, so "complexity doesn't help" is weaker than the abstract
   implies. The strong, defensible claim is that fuel data matters a lot.
2. Fuel is the single most important predictor globally (E1).
3. Leakage-aware validation is rare. Only the Australian study (E2) held out whole fire events
   and whole regions. Most Indian studies report AUC on unclear splits.
4. Spread forecasting is the weakest-evidenced area: ~1.5% of reviewed ML wildfire literature
   (E4), and the one end-to-end spread paper (E3) has numbers that do not reconcile internally.
5. Indian work is almost entirely static susceptibility mapping, labelled from MODIS/VIIRS
   hotspots, scored with AUC, rarely calibrated.
6. Across Indian studies, roads, settlements, farmland and land cover recur as top predictors.
   [mine] Consistent with human-dominated ignition.

---

## 3. Gaps identified (candidate openings for the project)

| # | Gap | Evidence | Strength of evidence |
|---|-----|----------|----------------------|
| 1 | Satellite detection misses most small fires in India | 5.64% of Uttarakhand incidents detected; <20% of burned area in central India | [UNVERIFIED] primaries not read |
| 2 | Official data conflicts by orders of magnitude | FSI 1,808.9 sq km vs state ~12 sq km for Uttarakhand 2023-24 | Both sources read; definitions differ |
| 3 | No validated Indian fuel model | None found in search | Absence of evidence, not proof of absence |
| 4 | No India-specific validated spread model / ROS dataset | None found | Same caveat |
| 5 | No documented forest-fire evacuation system for India | Only generic disaster SOPs found | Same caveat; MoEF&CC Sept 2024 guideline unread |
| 6 | Hotspot labels contaminated by agricultural burning | FSI masks mining/industry; a WB study stripped non-forest points | Sourced |

[mine] Gaps 3, 4 and 5 are "I could not find it", not "it does not exist". Each needs a
targeted check before being claimed as a contribution.

---

## 4. Options for small fires (NOT decided)

Feasibility ratings are my judgment for a first-year student project, not measurements.

| # | Option | What it addresses | Feasibility | Main risk |
|---|--------|-------------------|-------------|-----------|
| 1 | Ground sensor nodes (temp/humidity/smoke/gas) on LoRa | Minute-scale detection near villages and roads | Medium | Cost per sq km, power, theft, false alarms (sun, cooking smoke) |
| 2 | Camera towers with AI smoke detection | Early smoke over wide views | Low-Medium | Tower cost, fog/haze, power, connectivity |
| 3 | Sentinel-2 burn-scar mapping (10-20 m) | Builds our own small-fire labels; fixes gap 1 at training time | High | Not real-time; ~5-day revisit [general]; cloud |
| 4 | Community reporting (WhatsApp/app + verification) | Humans are first on scene; already happening in Uttarakhand | High | Unverified/duplicate reports; phone coverage |
| 5 | Risk-based patrol prioritisation | Where to look first, using danger forecast + roads/settlements | High | Only as good as the input data |
| 6 | Drones for verification | Confirms a flagged location | Low | Airspace regulation, range, weather |
| 7 | Commercial smallsat fire constellations | Higher resolution/revisit | Not buildable; possibly usable as data | Cost, access [UNVERIFIED they exist usefully] |

[mine] Initial read: options 3, 4 and 5 are software-only, cheap and fast to prototype, and
play to existing skills. Option 1 is the strongest hardware candidate and the only one giving
genuine early detection of small fires. Options 2, 6, 7 look out of reach at this stage.

CRITICAL CONSTRAINT [mine]: do not train a small-fire model on satellite hotspots alone —
it inherits exactly the blind spot the project is trying to fix. This is the main argument
for option 3 or 4 as a label source.

---

## 5. ML vs deep learning — evidence-based answer

Recommendation: gradient-boosted trees (XGBoost / LightGBM) as the baseline for tabular
prediction; neural networks only where the input is imagery or a space-time sequence.

Evidence:
- E1 tested random forest, XGBoost and a neural net on identical data: XGBoost best, neural
  net no better. Reviewer noted tree-ensemble superiority on tabular data is well established
  (Grinsztajn et al. 2022, cited in the paper).
- Indian studies: RF / XGBoost / SVM dominate; where deep learning was compared directly
  (Shome et al. 2025, Sikkim) RF still won. [UNVERIFIED — abstract only]

Task-to-model mapping:
| Task | Model | Why |
|------|-------|-----|
| Fire risk from tabular features | XGBoost / random forest | Best accuracy on tabular, fast, interpretable, modest data needs |
| Burn-scar segmentation from Sentinel-2 | CNN (U-Net) | Input is imagery |
| Smoke detection from camera images | CNN | Input is imagery |
| Spread over time on a grid | ConvLSTM, or physics / cellular automata | Needs space + time |

Methodological warnings carried over from the literature:
1. Split by region AND by year, never randomly — spatial autocorrelation inflates random-split
   scores. E2's leave-one-fire-out and leave-region-out is the pattern to copy.
2. AUC alone is misleading under heavy class imbalance. Report calibration (reliability curve,
   Brier score, ECE) if the output is a probability. E1 dropped precision in favour of ECE
   because its probabilities rarely exceed 5%.
3. Label quality caps achievable accuracy — E1's authors state the model can only ever be as
   good as the satellite it learned from. For Indian small fires that ceiling is low (gap 1).

---

## 6. Questions stage 2 must answer

Scope decisions (Ayush's, listed in his own stage plan):
- Digital twin, or ML only?
- Include evacuation?
- Include spread prediction?

[mine] Inputs to those decisions:
- A digital twin requires a spread model + live data feeds + continuous state updating. The
  only spread paper with a serious design (E3) does not reconcile internally; NYU's (E7) has
  no paper. Treat "digital twin" as high-risk until feasibility is tested.
- Evacuation scope depends entirely on who the user is — unresolved (below).
- Spread prediction depends on fuel data (gap 3) and on validation data (gap 2).

Unresolved and blocking:
- PRIMARY USER: forest department staff, district officials, villagers, or pilgrims/tourists?
  Asked three times in stage 1, still open. This determines whether evacuation is in scope and
  what "detection" even means.

---

## 7. Verification backlog

Primary sources not read:
- Kalaranjini et al. 2020 — source of the 5.64% Uttarakhand detection figure.
- Roy 2003 / Srivastava & Garg 2013 / Satendra & Kaushik 2014 — sources of "95% human-caused".
- MoEF&CC guideline, Sept 2024, on fire-susceptible areas.
- MoEF&CC + World Bank, "Strengthening Forest Fire Management in India" (2018) — the claim
  that 20 districts account for 47% of fire distribution.
- Kulhandjian (SJSU) full report — evacuation claims (5x detection, 28% faster evacuation,
  35% SAR efficiency) are unverifiable without it.
- The five Indian ML case studies (abstract-level only so far).
- Di Giuseppe supplementary material (train/test split still not confirmed from the paper
  itself; an ECMWF slide deck says MODIS 2010-2014 training, unconfirmed for this paper).

Checks to run:
- Dataset licences: FIRMS, FSI, Bhuvan, ERA5-Land, IMD, OSM, SRTM.
- Is the FSI Large Fire archive (since 2012) bulk-downloadable?
- Does any usable Indian fuel-type / fuel-load map exist?
- Has any Indian field trial of ground fire-detection sensors been published?
- Do small fires actually drive harm, or is harm concentrated in large fires?
- ECMWF PoF-Toolbox (Feb 2026, Jupyter notebooks on GitHub) — licence and usefulness as a
  starting point for a local Indian model.

---

## 8. Stage plan (Ayush's, recorded for reference)

1. Stage 1 (this): research, gaps, challenges. [current]
2. Stage 2: define the problem statement and the actual solution — digital twin vs ML only;
   evacuation in or out; spread prediction in or out.
3. Stage 3: feasibility analysis; innovate on overcoming the challenges.
4. Stage 4: extract all datasets.
5. Stage 5: model document — how to train, which model, advantages/disadvantages, how it
   helps in this scenario.
6. Stage 6: create the repository.
