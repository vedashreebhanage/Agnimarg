# integration/ — Connecting ML, imagery and the web app

How outputs from `imagery/` and `ml/` reach the backend and the dashboard.

What belongs here:
- Interface definitions: what each layer produces (format, grid, units, update frequency) and
  what the backend expects to receive.
- Glue code that turns model outputs into what `backend/` serves — for example, replacing the
  heuristic risk score in `backend/sentinel.py` with a trained model's output.

The software itself (API and dashboard) lives in `backend/` and `frontend/`.

Status: empty.
