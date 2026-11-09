# ml/ — AI/ML

Models, training and evaluation for Agnimarg.

What belongs here:
- Feature building for the risk layer (weather, terrain, vegetation/fuel proxies, human factors).
- Model training and evaluation code (gradient-boosted trees for tabular risk; neural networks
  only for imagery or space-time grids).
- Experiment records: random seeds, library versions, train/test split definitions.

What does not belong here:
- Raw or processed data, and trained model weights — these stay out of git (see `data/README.md`).
- Satellite download/preprocessing code — that is `imagery/`.

Rules (from `docs/PROBLEM_STATEMENT.md`, section 3.2): split by region and by year, never randomly;
report calibration (reliability curve, Brier score, ECE) alongside AUC; never train a small-fire
model on satellite hotspots alone; mask agricultural/industrial burning from hotspot labels.

Status: empty. The current prototype's risk score is a heuristic in `backend/sentinel.py`, not a
trained model.
