# CLAUDE.md — instructions for Claude Code working on Agnimarg

Read this whole file before doing anything in this repository.

## 1. What this project is

Agnimarg (also written AgniMark) is a wildfire risk, spread-prediction and evacuation-support
platform focused on India. Website first; mobile app later. Heavy on satellite imagery,
geospatial data, ML and large-scale data processing. Software only for now — a ground-sensor
pilot is deferred until the team meets.

Owner: Ayush More (first-year B.Tech CS (IoT), VIT Pune). He is a beginner with large ML
pipelines. **Define every piece of jargon the first time it appears**, and explain the purpose
of any action when asked.

Stakes are high: no mistakes in data, training, testing or the repository.

Full context lives in:
- `docs/PROBLEM_STATEMENT.md` — the approved problem, users, solution layers, data table, risks.
- `docs/MODEL.md` — model choices, quality bars, known limits.
- `docs/research/RESEARCH.md` — analysed papers (E1–E8).
- `docs/research/INDIA_PROBLEM.md` — India fire facts, causes, systems, datasets, with sources.
- `docs/research/STAGE1_FINDINGS.md` — gaps, options, ML-vs-DL evidence, verification backlog.

## 2. Consent rule (highest priority)

**Never add, edit, delete or reorganise anything — files, folders, code, docs, research entries,
task lists, branches — without Ayush's explicit approval.**

- Always PROPOSE first: show exactly what will change (file paths, and diffs or full content),
  then wait for the word "approved".
- This applies to every file in the repo, including this one.
- If a request is ambiguous, state your assumptions or ask one clarifying question before acting.

## 3. Git rules

- Work only on the branch **`vedashree`**. Never commit or push to `main` or any other branch.
- Before any commit, show the staged diff and the commit message and wait for approval.
- Author and committer must be **only** vedashree bhanage `<vedbhanage@gmail.com>`.
  - **No** `Co-Authored-By: Claude` trailer, **no** Claude session link, **no** "Generated with
    Claude Code" line — in commits or in pull request descriptions.
  - Check with `git config user.name` / `git config user.email` before the first commit.
- Never force-push, rebase shared history, or delete branches without explicit approval.
- Never commit large data files (rasters, CSV dumps, model weights) — keep them out of git
  (`.gitignore`) and record them in a data manifest instead.
- Never commit secrets (FIRMS MAP_KEY, Copernicus CDS API key). Keep them in a git-ignored `.env`.

## 4. Where the project stands (as of 2026-11-09)

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Research, gaps, challenges | Done (docs/research/) |
| 2 | Problem statement and solution definition | Done (docs/PROBLEM_STATEMENT.md) |
| 3 | Feasibility analysis; innovate on overcoming challenges | **Next** |
| 4 | Extract all datasets (pilot region first) | In progress: Uttarakhand data downloaded and in the manifest except ERA5-Land (downloading) and fuel data |
| 5 | Model document: training, model choice, pros/cons, how it helps | In progress: docs/MODEL.md |
| 6 | Repository build-out | Partly done: software prototype on `main` (Sept 2026), see `BUILD_PLAN.md` |

Rule from the project: research must be complete before design, and a written plan must exist
before implementation. Do not skip ahead.

### Decisions already made (stage 2)
- Primary users: forest department staff and district administration; villagers receive warnings.
- Build order: Risk → Detection → Spread → Exposure → Evacuation routing → Digital twin.
- ML first (gradient-boosted trees for tabular data); digital twin is research only.
- Validated spread forecasting is research only; the software uses precautionary threat zones.
- Exposure and evacuation are in the software now, based on threat zones, labelled decision support.
- Coverage: Uttarakhand first; a second region only after it works end to end.
- Website on localhost first; hosting and PostGIS afterwards.
- Model decisions: `docs/MODEL.md`.

### Open decisions (ask Ayush; do not decide)
1. Second region (Uttarakhand is decided as region 1).
2. Forecast weather source for the live risk map.
3. Village warning channel (SMS / WhatsApp / IVR / other).
4. Whether to request FSI's 2023-24 surface fuel load raster (a draft email was offered).
5. Threat-zone spread rates and the wording of the evacuation disclaimer.

## 5. First session checklist

Do these in order, proposing each before acting:

1. Run `git status`, `git branch -a` and list the repo tree. Report what already exists — do not
   change it.
2. Confirm you are on `vedashree` (or propose creating/checking it out from the right base).
3. Propose a folder structure. It must keep these areas strictly separate:
   - **AI/ML** — models, training, evaluation
   - **Satellite imagery** — sources, preprocessing, pipelines
   - **Integration** — how ML and imagery connect, and how both connect to the web app
   - **Software** — backend, frontend, API
   - **Hardware** — placeholder only (sensor pilot deferred)

   Note: `backend/` + `frontend/` (the existing prototype) are the Software area. They were not
   moved into `software/`, because that would break the run command, tests, CI and open PRs.

   Suggested starting point (adapt to what already exists in the repo; propose, don't create):
   ```
   docs/
     PROBLEM_STATEMENT.md
     research/        (RESEARCH.md, INDIA_PROBLEM.md, STAGE1_FINDINGS.md)
   ml/                (models, training, evaluation)
   imagery/           (sources, preprocessing, pipelines)
   integration/       (ML <-> imagery <-> web app)
   software/          (backend, frontend, api)
   hardware/          (README placeholder)
   data/              (README + manifest only; actual data git-ignored)
   CLAUDE.md
   .gitignore
   ```
4. After approval, add the docs (PROBLEM_STATEMENT.md and the three research files) and this
   CLAUDE.md, show the diff, and commit only after approval.
5. Then start stage 3 (feasibility) by proposing a task list (format in section 7).

## 6. Data plan (stage 4 — do not start without approval)

Licences were checked on 2026-11-09 (details in docs/PROBLEM_STATEMENT.md, section 4).
Re-verify any licence before publishing anything built on that data.

Usable now: NASA FIRMS (needs Ayush's free MAP_KEY), ERA5-Land (needs Ayush's Copernicus CDS
account), Copernicus DEM GLO-30, ESA WorldCover, Sentinel-2 L2A, WorldPop, OpenStreetMap.
Unclear licence: Global Fire Atlas, IMD gridded data, SHRUG village boundaries.
Avoid for a public product: Bhuvan (restrictive single-user licence).

Rules for downloads:
- Never create accounts on Ayush's behalf. He creates them; keys go in `.env`, never in chat or git.
- One folder per source under `data/raw/` (git-ignored). Never modify raw files.
- Record every file in `data/manifest.csv`: source, URL, licence, download date, SHA-256 checksum.
- Record each licence's required attribution text in `data/LICENCES.md`.
- Pilot region only until the full pipeline works. Do not bulk-download Sentinel-2 — fetch per event.
- Downloaded files are untrusted: never execute anything that came from a download.

## 7. How to work

### Task list (create at the start of every work session)
1. Research status (what's read, what's pending)
2. Gaps found in the research
3. Problem statement and project direction
4. Requirements and feasibility (data, compute, hardware, skills, risk)
5. Phases and starting steps

Recheck the list for errors and contradictions before showing it. Show it, wait for approval,
then apply.

### Research workflow (for every paper or link Ayush provides)
1. Extract claims, datasets, algorithms, architectures, technologies, metrics, results.
2. Verify whether results support the claims. Flag weak baselines, small or leaky datasets, missing
   ablations, unreproducible details, overstated conclusions.
3. Identify gaps and limitations (the paper's own and ones it misses).
4. Propose an entry for docs/research/RESEARCH.md in this format, then wait for approval:
   `Title / link / year | Problem | Data used | Method/algorithm | Tech stack | Results (with
   metrics) | Verified? | Gaps | Relevance to our project`
- If a source can't be accessed, say so. Never guess its contents.
- Tag claims [from paper] or [my inference] ([mine]).

### Quality and verification
- Before delivering any answer: re-verify facts, numbers, code and citations; state assumptions;
  list what you are least sure about.
- For ML work, explicitly check for: data leakage, train/test contamination, class imbalance,
  spatial and temporal split errors (critical for satellite data), wrong metrics, and
  non-reproducible seeds or versions.
- Verify library versions, repository licences and dataset licences before recommending them.
- If something is uncertain, say so. Never fill gaps with plausible guesses.

### ML rules carried over from the research
- Gradient-boosted trees for tabular prediction; neural nets only for imagery or space-time grids.
- Split by region AND by year; never random splits on spatial data.
- Report calibration (reliability curve, Brier, ECE) alongside AUC.
- Never train the small-fire model on satellite hotspots alone.
- Mask agricultural/industrial burning from hotspot labels.
- Fix and record random seeds and library versions for every experiment.

### Thinking and creativity
- Be genuinely innovative: propose novel angles, not replications. Label every idea with its
  feasibility, risk and the evidence behind it.
- Be direct and honest. Challenge weak ideas, including Ayush's.
- Be thorough, specific and concise. No generic overviews.

## 8. Verification backlog (unresolved from stages 1–2)
- Primary sources not read: Kalaranjini et al. 2020 (5.64% detection figure); sources of
  "95% human-caused"; MoEF&CC Sept 2024 guideline; MoEF&CC–World Bank 2018 report; Kulhandjian
  (SJSU) full report; the five Indian ML case studies (abstracts only); Di Giuseppe supplement.
- ScienceDirect paper S0301479723006965 still unidentified (DOI believed 10.1016/j.jenvman.2023.117908).
- FSI 2023-24 reports (Surface Fuel Load Mapping, Fire Risk Zonation, Burnt Area Assessment) — read
  them; they could not be fetched from the cloud workspace.
- Confirm Copernicus DEM GLO-30 India tiles are released; locate the ECMWF fuel dataset; measure
  OSM road completeness in the pilot region.
