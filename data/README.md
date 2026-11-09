# data/ — Data records (no data files in git)

Downloaded data never goes into git. This folder holds only the records about it.

- `manifest.csv` — one row per downloaded file: file, source, url, licence, download_date,
  sha256 (checksum), notes.
- `LICENCES.md` — the attribution text each data licence requires, copied from the source page.
- `raw/` — downloaded files, one folder per source, never modified. Git-ignored.
- `processed/` — files derived from `raw/`. Git-ignored.

Rules: keys (FIRMS MAP_KEY, Copernicus CDS API key) go in a git-ignored `.env`, never in code or
chat. Downloaded files are untrusted: never run anything that came from a download.

## Existing data outside this folder

`dataset/` (top level) already contains 7 NASA FIRMS CSV files committed on 2026-09-24. Their
source URL, download date, area/date range and checksums are not yet recorded. To do: get these
details from the teammate who added them, then add them to `manifest.csv`.
