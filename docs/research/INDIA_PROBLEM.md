# INDIA_PROBLEM.md: wildfires in India — problem brief

Agnimarg stage 1. Drafted 2026-11-04. Not yet reviewed by Ayush.

Convention:
- Unmarked statements come from the cited source.
- [mine] = my own inference or arithmetic, not from any source.
- [general] = standard textbook fire science, not re-verified against a source in this session.
- [UNVERIFIED] = reported by a secondary source; primary source not read.

---

## 1. Fire science basics

### 1.1 The fire triangle [general]
A fire needs heat (ignition), fuel (dry vegetation) and oxygen. Removing any one stops it.
This is why suppression works by clearing fuel (fire lines), cooling (water) or smothering.

### 1.2 Fire types [general]
- Ground fire: burns slowly underground in roots/humus; can smoulder for days.
- Surface fire: burns leaf litter and grass; the most common type.
- Crown fire: spreads through tree canopies; fast and violent.
A fire can transition between types depending on fuel, slope and weather.

### 1.3 What governs spread — the fire behaviour triangle [general]
Fuel:
- Fuel load (dry mass per unit area): more fuel, more intensity.
- Fuel moisture: drier fuel ignites and spreads faster.
- Fuel type and continuity: continuous litter carries fire; gaps break it.
Weather:
- Wind speed and direction: usually the dominant driver; also carries embers.
- Temperature: higher temperature dries fuel.
- Relative humidity: lower RH dries fuel.
- Rainfall and dry-spell length: sets background dryness.
Terrain:
- Slope: fire runs faster uphill (flames preheat fuel above).
- Aspect: sun-facing slopes are drier.
- Elevation and valley shape: drive local winds.

Two terms that matter for modelling:
- Spotting: embers carried ahead of the front, starting new fires. Grid/cellular-automata
  models represent this poorly (Moldamurat et al. 2026 concede this; see RESEARCH.md E3).
- Rate of spread (ROS): speed of the fire front (e.g. m/min); classically from the
  Rothermel model combining fuel, wind and slope. [general]

---

## 2. Scale of the problem in India

### 2.1 Season
- Nov–June nationally, peak Feb–May (FSI; NDRF document).
- Uttarakhand's official season: 15 Feb – 15 June (Uttarakhand Forest Department, via ETV Bharat).

### 2.2 Fire-prone area (ISFR 2023, share of forest cover + scrub)
- Extremely fire prone: 1.45% (11,018.24 sq km)
- Very highly fire prone: 9.89% (75,084.02 sq km)
- Highly fire prone: 16.63% (126,187.87 sq km)
- Total extremely-to-highly: 27.97% (confirmed by Rajya Sabha reply, 13 Mar 2025)
- Extremely-to-very-highly: 11.34%
CAUTION: older figures circulating online (35.46% fire-prone; 2.81% / 7.85%) are from earlier
ISFR editions with different category definitions. Do not mix editions. [mine]

### 2.3 Detection counts (NOT distinct fires)
FSI's "number of forest fires" = satellite detections, including large, continuous and
repeated fires (ministry's own wording). Season totals (SNPP-VIIRS):
- Nov 2020 – Jun 2021: 345,989
- Nov 2021 – Jun 2022: 223,333
- Nov 2022 – Jun 2023: 212,249

### 2.4 Season 2023-24 (FSI, reported via Tribune India)
Detections: Uttarakhand 21,033 (highest); Odisha 20,973; Chhattisgarh 18,950;
Andhra Pradesh 18,174; Maharashtra 16,008; Madhya Pradesh 15,878; Telangana 13,479.
Himachal Pradesh rose from 704 to 10,136 (rank 24 -> 8).
Fire-affected area (first time FSI estimated this): Andhra Pradesh 5,286.76 sq km;
Maharashtra 4,095.04; Telangana 3,983.28; Uttarakhand 1,808.9.
Note: the Tribune headline says "74% rise" for Uttarakhand but 21,033 vs 5,351 is ~4x. [mine]

### 2.5 Burnt area vs detections
A 2014 AWiFS (Resourcesat-2) assessment estimated 57,127.75 sq km of vegetation burnt
(~7% of India's forest cover), with dry deciduous forests worst affected; highest burnt area
in Odisha, then Andhra Pradesh, Maharashtra, Chhattisgarh.
[mine] Implication: central/peninsular India has the largest AREA burning; the Himalaya has
the most visible threat to people. These are two different problems.

### 2.6 Human cost
- 12 deaths in Uttarakhand's 2024 fire season — deadliest since 2021 (8 deaths)
  (Hindustan Times).
- 5 deaths reported by early May 2024, with 910 fires and 1,145 ha affected
  (SPHERE India situation report, 7 May 2024).

---

## 3. Causes of fires in India

### 3.1 Human vs natural
- NDRF: majority man-made; natural fires (lightning, dry bamboo friction) "very rare".
- "~95% human-caused" is very widely repeated (Roy 2003; Srivastava & Garg 2013;
  Satendra & Kaushik 2014, as cited in a JTFS 2024 review). [UNVERIFIED — primary sources
  not read]
- Counter-point worth keeping: ecologist Raman Sukumar (IISc) said the natural-vs-human
  proportion "remains largely unknown", while agreeing humans cause a major share (Eos).
- Strongest direct evidence: 83.4% reduction in cumulative fire incidence in the Western
  Himalaya during the COVID lockdown (24 Mar – 5 May 2020) vs the 15-year average
  (Gupta, Bhatt, Roy & Chauhan, IIRS/ISRO, Current Science 2020).
[mine] Recommendation: write "most fires are human-caused" rather than "95%" unless the
primary source is located.

### 3.2 Regional clusters (NDRF document)
a) Western Himalaya (J&K, Uttarakhand, Himachal): pine forests + transhumant pastoralists.
d) North-East: shifting cultivation (jhum).
(Only clusters a and d were captured from the NDRF PDF; secondary sources describe the
other two as central Indian dry deciduous forest and the southern Western/Eastern Ghats.)

### 3.3 Specific ignition sources cited
Careless disposal of cigarettes/beedis; escaped agricultural/crop-residue burning; burning
of pine needles by villagers to promote grass for cattle; campfires; deliberate arson;
electrical faults; industrial activity near forests; increased tourist/pilgrim traffic
(Badrinath-Kedarnath was the 2026-season hotspot during Char Dham Yatra, per ETV Bharat).

### 3.4 Fuel conditions
- Chir pine (Pinus roxburghii) needles in the Western Himalaya: high resin, highly flammable.
- Dry deciduous forest litter in central India.
- Trees shedding dry leaves from mid-February in Uttarakhand (forest officials).

### 3.5 Weather trigger
Dry spells + high temperature. The 2024 Uttarakhand season was described as having
essentially no rainfall, with western disturbances reaching Himachal but not Uttarakhand
(ThePrint).

### 3.6 Spatial pattern
"Most forest fires occur in areas close to villages or roads" — Rajendra Rawat, forest guard,
Dasholi block (Down To Earth).
[mine] This matches the Indian ML studies in RESEARCH.md E5, where distance to roads and
settlements are consistently top predictors.

### 3.7 Attribution is politically sensitive
Van Gujjars (a transhumant pastoral community) and villagers are routinely blamed for fires;
commentary disputes this and documents their participation in fire lines and water holes
(The Bastion). [mine] Any cause-attribution feature in a product needs care here.

---

## 4. Intensity and spread — what is NOT known

- No India-wide statistics found on flame length, fire radiative power (FRP) or rate of spread.
- FSI uses proxies: Large Fire Events (threshold of juxtaposed SNPP-VIIRS pixels, tracked
  across passes) and burnt-area estimates.
- No validated Indian fuel model or fuel-load dataset found. [mine] This is the single biggest
  modelling gap, because fuel was the most important predictor in the strongest study
  reviewed (RESEARCH.md E1).
- Spread drivers for India are documented only qualitatively.

---

## 5. Data reality check (the most important finding for a product)

### 5.1 Satellite detection misses most fires
- MODIS/VIIRS products identified only 5.64% of fire incidents in Uttarakhand
  (Kalaranjini et al. 2020, as cited in a Frontiers in Forests and Global Change paper).
  [UNVERIFIED — primary not read]
- FIRMS burned-area detection in central India: <20% (Frontiers paper, using 30 m Landsat).
- MODIS has low probability of detection in South/Southeast Asia because fires are small
  (Giglio et al., as cited in the same paper).

### 5.2 Official sources conflict badly
Uttarakhand 2023-24:
- FSI satellite estimate: 1,808.9 sq km affected.
- State forest department: ~1,145-1,196 hectares by May 2024 (~11.5-12 sq km).
  [mine] That is a ~150x discrepancy. Likely different definitions (satellite thermal
  footprint vs recorded incident damage), but it means neither can be used as ground truth
  without understanding the definitions.
- State-recorded incidents: 1,276 (2024), 268 (2025), 773 (2023), 2,186 (2022), 2,813 (2021)
  (ETV Bharat) vs 21,033 satellite detections for 2023-24.
[mine] The widely quoted "28-fold increase in alerts since 2019-20" may partly reflect
changes in detection/reporting rather than purely more fires.

### 5.3 False positives
- FSI applies a filter to mask fires from mining and industrial areas.
- FSI states explicitly that detections are "thermal anomalies" and ground incidence may differ.
- Agricultural/stubble burning appears in FIRMS data; a West Bengal study used BIS and Bhuvan
  land-cover layers to strip non-forest fire points.
[mine] For an India model trained on hotspots, crop-residue burning contamination is a
real risk and must be masked.

---

## 6. Existing systems

### 6.1 FSI Forest Fire Alert System (FAST 3.0)
- Sensors: MODIS (1 km, Aqua/Terra) since 2004; SNPP-VIIRS (375 m) since 2017.
- Passes used: MODIS 10:30 am/pm and 1:30 am/pm; SNPP 1:30 am/pm (Tamil Nadu Forest Dept page).
- Pipeline: NASA active-fire data -> ISRO NRSC Shadnagar earth station -> FSI Dehradun ->
  automated alert generation -> SMS/email to registered users; feedback form per alert.
- Three alert types: pre-fire (weekly, one-week validity, uses Canadian FWI + forest types +
  IMD data, shared via SACHET portal); near-real-time at overpass; Large Forest Fire alerts.
- Large Fire Monitoring launched 16 Jan 2019: Python scripts identify candidate large fire
  events from thresholds of juxtaposed VIIRS pixels and track them across passes; archive
  back to 2012.
- Coverage: beat-level alerts for 20 states; district level elsewhere.
- Users: >50,000 registered (FSI paper, 2019-20 era).
- Stack (per FSI's own paper): Python, open-source MapServer geoportal, WMS/WFS, bulk SMS,
  MySQL, PHP web portal. Described as "the largest forestry application in India".
- Van Agni geoportal: https://vanagniportal.fsiforestfire.gov.in/
- FSI also did Forest Fire Risk Zonation mapping for the West Himalayan region (static factors).

### 6.2 ISRO / NRSC
- Active fire alerts disseminated via Bhuvan geoportal.
- Burnt-area assessment on request (rapid during season, total post-season), using AWiFS
  and Sentinel-2.
- NESAC: forest fire vulnerability zonation maps for all NE states; daily fire hazard alerts.

### 6.3 Policy and schemes
- Forest Fire Prevention and Management (FPM) scheme — the main centrally sponsored scheme.
- National Action Plan on Forest Fires.
- Wildfire Management Plan 2015 (covering 52 elephant corridors) [UNVERIFIED].
- MoEF&CC guideline dated Sept 2024 on fire-susceptible areas, following a 9 Jul 2024
  direction involving MoEF&CC and NDMA — document found but NOT read.
- "Strengthening Forest Fire Management in India" — MoEF&CC + World Bank report (2018);
  reported finding: 20 districts account for 47% of fire distribution. [UNVERIFIED]

---

## 7. Mitigation and response on the ground

### 7.1 Prevention
- Fire lines: strips cleared of dry leaves/litter that fire cannot cross (documented in
  Garhwal/Kumaon).
- Controlled/planned small burns organised by villagers.
- Clearing dry foliage before the season; water points.
- Awareness meetings, village pledges, monthly reminders.
- Watch towers and fire watchers (MoEF&CC's four stated strategies: watch towers, fire
  watchers, community engagement, fire lines).

### 7.2 Suppression
- Beating flames with green branches; rakes; fire kits (rake, water bottle, torch,
  protective jacket) distributed to trained villagers.
- NDRF and Indian Air Force deployed in severe seasons (Uttarakhand 2024).
- Fire crew stations: 1,438 established in Uttarakhand (SPHERE report, May 2024).

### 7.3 Community institutions
- Van Panchayats: village forest councils, Uttarakhand, under the Van Panchayat Act 1931;
  12,167 managing 7,326.88 sq km (ISFR 2019, quoted in Policy Circle).
  One commentary claims only ~30% remain functional [UNVERIFIED].
- Mahila Mangal Dals: village women's groups (12 elected women each); described by the
  Uttarakhand CM in May 2025 as first responders in villages.
- Gram Panchayat-level forest fire safety committees.
- Joint Forest Management committees.
- Documented success: Marhmanley village (Kamla Devi, van panchayat head) kept free of major
  blazes for three consecutive years through organised, planned small burns (Mongabay).
- WhatsApp groups used for village-level fire coordination (Earth Journalism Network).

### 7.4 Helpline
1800 180 4141 (Uttarakhand forest fire helpline) and 7668304788 (state control room),
per SPHERE India situation report. [UNVERIFIED]

---

## 8. Evacuation in India

NO documented forest-fire-specific evacuation system was found.

What exists:
- Disaster Management Act 2005; NDMA issues national guidelines; NDRF provides response force;
  District Magistrate holds district-level authority.
- MHA Standard Operating Procedure for Responding to Natural Disasters (2010) lists "rapid
  evacuation of threatened communities" as a generic response element, and names the Forest
  Department among responding agencies. Not fire-specific.
- NDMA + MoEF&CC workshop "Forest Fire and Its Challenges" (Oct 2024): three-point strategy of
  prevention, preparedness and community involvement; emphasis on training forest guards and
  local volunteers. No evacuation framework reported.
- NDMA guidelines exist for cyclones (with evacuation planning chapters) but no equivalent
  forest-fire guideline was found.

[general] Core evacuation logic: warning -> movement along a route -> safe location. The
decisive quantity is fire arrival time at a settlement vs time required to evacuate it.
[mine] In Himalayan villages with steep, narrow roads that margin may be very short — and
this appears to be genuinely open ground for the project.

---

## 9. Datasets (inventory; licences NOT verified for any entry)

Fire labels:
- NASA FIRMS (MODIS 1 km, VIIRS 375 m): active fire detections, near-real-time + archive.
- FSI portals: NRT alerts, Large Fire Event archive since 2012, state-wise counts.
- data.gov.in: season/state-wise counts from Parliament replies (counts only).
- Sentinel-2 (10-20 m) / Landsat (30 m): burn-scar mapping — must be computed by us.
- Global Fire Atlas (2003-2016): fire size, duration, speed, direction — relevant to spread
  but built on coarse satellite burned area.

Weather:
- ERA5-Land (9 km, daily): temperature, dew point, wind, precipitation. Free via Copernicus.
- IMD: Indian met data — access terms unknown.

Fuel / vegetation:
- NDVI / NDWI from Sentinel-2 or MODIS.
- Bhuvan: forest fraction (5 km; 1930, 1975, 2013), land use/land cover.
- BIS LULC at 1:50,000.
- FSI forest type map.
- NO validated Indian fuel-load / fuel-moisture dataset identified.

Terrain:
- SRTM DEM (30 m): elevation, slope, aspect.

Ignition / human:
- OpenStreetMap: roads, settlements.
- Census 2011: population.
- Distance-to-farmland layers (derived).

Exposure (for evacuation):
- Village locations, road network, population.

---

## 10. Gaps and openings

1. Detection gap: satellite alerts miss the majority of small fires in India.
2. Data trust gap: official sources disagree by orders of magnitude; no reliable ground truth.
3. Fuel gap: no validated Indian fuel model, yet fuel is the most important predictor.
4. Spread gap: no India-specific validated spread model or rate-of-spread dataset found.
5. Evacuation gap: no documented forest-fire evacuation system.
6. Label contamination: agricultural burning in hotspot products.
[mine] All six are inferences about where a project could contribute; none is a decision.

---

## 11. Open questions before stage 2

- Who is the primary user: forest department staff, district officials, villagers, or
  pilgrims/tourists? This determines whether evacuation is in scope.
- Do small fires actually matter for harm, or is harm concentrated in large fires?
  (Many small fires are low-intensity ground/surface fires.)
- Has any Indian field trial of ground fire-detection sensors been done?
- Are FIRMS / FSI / Bhuvan data licences permissive for a product?
- Is the FSI Large Fire archive bulk-downloadable?
- Does any usable Indian fuel-type map exist?
- Primary sources still unread: Kalaranjini et al. 2020 (5.64%); the "95% human" sources;
  MoEF&CC Sept 2024 guideline; MoEF&CC-World Bank 2018 report.

---

## Sources
- Rajya Sabha unstarred Q.1640, 13 Mar 2025: https://rsdebate.nic.in/bitstream/123456789/757377/1/PQ_267_13032025_U1640_p1015_p1017.pdf
- FSI FAST 3.0 technical note: https://fsiforestfire.gov.in/libraries/assets/documents/technical-information-series-v1-n2.pdf
- FSI NRT workflow: https://fsiforestfire.gov.in/Home/NRTDetails
- Tamil Nadu Forest Dept, FSI alert system: https://forests.tn.gov.in/pages/view/Forest_Fire_Alert_Systems
- Morung Express on ISFR 2023 fire categories: https://morungexpress.com/forest-fires-decline-in-nagaland-by-over-31-highlights-isfr-2023
- Tribune India, Uttarakhand/FSI season data: https://www.tribuneindia.com/news/delhi/uttarakhand-sees-74-rise-in-forest-fires-worst-hit-in-country
- SPHERE India situation report, 7 May 2024: https://www.sphereindia.org.in/sites/default/files/2024-05/Sitrep-1__Forest%20Fire%20in%20UK_07-05-2024.pdf
- NDRF forest fire document: https://www.ndrf.gov.in/sites/default/files/Forset%20Fire.pdf
- Gupta et al., Current Science 2020 (COVID lockdown): https://mail.i-scholar.in/index.php/CURS/article/download/205571/191568
- Eos coverage of the same: https://eos.org/articles/covid-19-lockdown-reduces-forest-fires-in-the-western-himalayas
- Frontiers in Forests and Global Change, central India burned area: https://frontiersin.org/journals/forests-and-global-change/articles/10.3389/ffgc.2022.933807/pdf
- AWiFS burnt area assessment 2014: https://i-scholar.in/index.php/CURS/article/view/142151/130418
- NRSC fire/drought slides: https://www.nrsc.gov.in/sites/default/files/pdf/ebooks/drm/S-V_ForestFireDrought.pdf
- NESAC NE forest fire assessment: https://nesac.gov.in/assets/resources/2020/12/Forest-Fire-Assessment-in-NER.pdf
- ETV Bharat, Uttarakhand statistics: https://www.etvbharat.com/en/state/fire-in-the-sky-how-dry-spell-early-summer-high-heat-threatens-forest-fires-in-uttarakhand-enn26031101425
- ETV Bharat, Badri-Kedar hotspot: https://www.etvbharat.com/en/bharat/uttarakhand-forest-fires-down-but-badri-kedar-region-now-biggest-hotspot-enn26050602478
- Down To Earth, Uttarakhand community response: https://www.downtoearth.org.in/forests/how-uttarakhands-women-and-villages-are-defending-forests-with-community-care-and-smart-tools
- Earth Journalism Network version of the same story: https://earthjournalism.net/stories/how-uttarakhands-women-and-villages-are-defending-forests-with-community-care-and-smart
- Mongabay, women and wildfires: https://news.mongabay.com/short-article/2026/10/women-shoulder-the-burden-of-expanding-wildfires-in-rural-india/
- The Bastion, Van Gujjars and fire politics: https://thebastion.co.in/politics-and/the-hidden-politics-of-forest-fire-management-in-uttarakhand-the-van-gujjar-experience/
- Policy Circle, van panchayats: https://www.policycircle.org/environment/forest-fires-of-uttarakhand/
- ETV Bharat, NDMA-MoEF&CC workshop Oct 2024: https://www.etvbharat.com/en/!bharat/delhi-meet-emphasis-on-community-centric-approach-to-deal-with-forest-fire-in-india-enn24102406604
- MHA SOP for Responding to Natural Disasters (2010): https://erc.mp.gov.in/Documents/doc/Guidelines/ERC/SOP_disaster.pdf
- ThePrint, Uttarakhand April 2024 fires: https://theprint.in/india/5710-forest-fires-in-april-alone-uttarakhands-burning-problem-whats-behind-it/2062428
- Down To Earth, FAST 3.0 launch: https://www.downtoearth.org.in/forests/india-to-get-real-time-forest-fire-alert-system-62857
- FSI large fire monitoring paper (Vikram et al. 2019): https://revistaeletronica.icmbio.gov.br/index.php/BioBR/article/view/1139
- Vidyasagar University, FIRMS vs FSI comparison: https://ir.vidyasagar.ac.in/handle/123456789/7554
- JTFS 2024 review of Indian forest fire causes: https://jtfs.frim.gov.my/jtfs/article/download/2724/1944/3709
