# Data licences and required attribution

One section per data source, added when the first file from that source is downloaded.
Copy the attribution wording exactly from the source's licence page, and record where it came from.
Anything marked **TO CONFIRM** could not be read from the source and must not be filled from memory.

Template:

## <Source name>
- Licence:
- Licence page URL:
- Checked on (date):
- Required attribution text (exact):
- Restrictions:

---

## Copernicus DEM GLO-30
- Licence: free licence for GLO-30 (ESA user licence for Copernicus Contributing Missions data)
- Licence page URL: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- Checked on (date): 2026-11-09
- Required attribution text (exact), when distributing or communicating to the public:
  "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
- Required attribution text (exact), where the data have been adapted or modified:
  "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
- Citation DOI: https://doi.org/10.5270/ESA-c5d3d65
- Restrictions / notes: the source page says the datasets "will be maintained until 2026".

## ESA WorldCover 10 m 2021 v200
- Licence: CC BY 4.0
- Licence page URL: https://esa-worldcover.org/en/data-access
- Checked on (date): 2026-11-09
- Required attribution text (exact; the page gives "[year]", filled here with 2021):
  "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium"
- Citation: Zanaga, D. et al., 2022. ESA WorldCover 10 m 2021 v200. https://doi.org/10.5281/zenodo.7254221
- Restrictions / notes: do not compare against the 2020 v100 map as "change"; ESA notes the algorithm differs between versions.

## WorldPop 2020 constrained (100 m)
- Licence: CC BY 4.0
- Licence page URL: https://hub.worldpop.org/data/licence.txt
- Checked on (date): 2026-11-09
- Required citation (exact, from the WorldPop API record):
  "Bondarenko M., Kerr D., Sorichetta A., and Tatem, A.J. 2020. Census/projection-disaggregated gridded population datasets for 189 countries in 2020 using Built-Settlement Growth Model (BSGM) outputs. WorldPop, University of Southampton, UK. doi:10.5258/SOTON/WP00684"
- Restrictions: none beyond attribution.

## OpenStreetMap (via Geofabrik, India central zone)
- Licence: Open Data Commons Open Database License (ODbL)
- Licence page URL: https://www.openstreetmap.org/copyright
- Checked on (date): 2026-11-09
- Required attribution: credit OpenStreetMap and its contributors, and make clear the data is available under the ODbL (the page says linking to its copyright page does this). Exact notice string: **TO CONFIRM** from the OSM attribution guidelines.
- Restrictions: share-alike. If we alter or build upon the data, we may distribute the result only under the same licence.

## geoBoundaries gbOpen IND ADM1 (commit 9469f09)
- Licence: source data CC BY 2.5 India (CC BY 2.5 IN); source DataMeet India community / Election Commission of India, year represented 2011
- Licence page URL: https://github.com/datameet/maps (licence source named in the geoBoundaries API record)
- Checked on (date): 2026-11-09
- Citation requested by geoBoundaries (exact short form):
  "Runfola, D. et al. (2020) geoBoundaries: A global database of political administrative boundaries. PLoS ONE 15(4): e0231866. https://doi.org/10.1371/journal.pone.0231866"
- Restrictions / notes: not Survey of India boundaries. Check India's map rules before publishing any public map.

## Copernicus Sentinel-2 L2A (Element 84 Earth Search, AWS)
- Licence: "Access to Sentinel data is free, full and open" (AWS Registry of Open Data), under the Copernicus Sentinel Data Legal Notice
- Licence page URL: https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- Checked on (date): 2026-11-09
- Required attribution text (exact): **TO CONFIRM**. The legal notice is a PDF that could not be read on this machine.
- Restrictions: per the legal notice (TO CONFIRM).

## Global Fire Atlas update (Andela & Jones), Zenodo v20250411
- Licence: CC BY 4.0
- Licence page URL: https://zenodo.org/records/14065246
- Checked on (date): 2026-11-09
- Citation: Andela, N. and Jones, M. W., "Update of: The Global Fire Atlas of individual fire size, duration, speed and direction", Zenodo, https://doi.org/10.5281/zenodo.14065246. Original paper: Andela et al. 2019, Earth System Science Data 11, 529, https://doi.org/10.5194/essd-11-529-2019
- Restrictions: none beyond attribution.

## IMD Pune gridded data (rainfall 0.25 deg; Tmax/Tmin 1 deg)
- Licence: none published. The site disclaimer says the data "should not be reproduced anywhere without prior permission".
- Licence page URL: https://imdpune.gov.in/disclaimer.html
- Checked on (date): 2026-11-09
- Required citation: **TO CONFIRM** (IMD links a reference paper, ref_paper_MAUSAM.pdf, on its rainfall page; not read).
- Restrictions: internal use only. Do not redistribute the data, or publish maps or products built from it, without IMD's permission.

## NASA FIRMS (files in `dataset/`)
- Licence: NASA open data, provided "as is"; FIRMS advises against use for local tactical decisions
- Licence page URL: **TO CONFIRM** (exact FIRMS data-use page)
- Checked on (date): 2026-11-09 (summary in docs/PROBLEM_STATEMENT.md, section 4)
- Required citation: **TO CONFIRM**
- Restrictions: decision support only; evacuation outputs must carry a disclaimer.
