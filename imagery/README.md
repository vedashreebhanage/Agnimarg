# imagery/ — Satellite imagery

Sources, preprocessing and pipelines for satellite and geospatial raster data.

What belongs here:
- Code that fetches imagery and rasters (Sentinel-2 L2A per fire event, Copernicus DEM GLO-30,
  ESA WorldCover, and others listed in `docs/PROBLEM_STATEMENT.md`, section 4).
- Preprocessing: clipping to the pilot region, reprojection, cloud masking, indices such as NDVI,
  burn-scar mapping.

What does not belong here:
- The downloaded files themselves — they go in `data/raw/` (git-ignored) and are recorded in
  `data/manifest.csv`.
- Model training — that is `ml/`.

Rule: do not bulk-download Sentinel-2; fetch per event, pilot region only until the pipeline works.

Status: empty.
