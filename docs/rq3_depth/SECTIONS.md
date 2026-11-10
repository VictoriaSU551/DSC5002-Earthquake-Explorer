# Regional cross-sections

View order is Regional projection, Cross-section, and 3D hypocentres. Regional projection is the default and Japan is the initial section region. All figure labels and endpoint descriptions are in English.

Section region preserves the catalogue group names in all three views, including Other regions. The specific local section name appears below the figures. Other regions is the global residual group; its local section example is southern Hikurangi, New Zealand.

The route map marks A as Start with a circle and B as End with a square. The section reads from A to B, left to right. Its zero-distance tick is labelled Trench. Matching start/end descriptions and coordinates appear below both plots.

Each cross-section uses a named local tectonic setting. The accompanying map and section contain the same event IDs. Regional projection and the existing 3D view use the full selected catalogue region. The Other cross-section samples southern Hikurangi in New Zealand, within the global residual category.

The fixed project catalogue covers 2000–2025 UTC and preferred magnitude M >= 5. Depth classes are <70 km, 70 to <300 km, and >=300 km. Negative reported depths are retained and missing depths are excluded from sections.

All local sections use the spherical PB2002 boundary intersection as zero distance, a window from -200 to +1,200 km, a 100 km half-width, a depth axis from -10 to 720 km, and equal kilometre scales. The selection requires both the along-route distance and the cross-route distance to fall inside the finite sampling strip.

Endpoints are project choices. References describe the regional tectonic setting. Route directions approximate cross-margin directions. Interpret each plot within its mapped sampling strip.

| Catalogue region | Local setting | Known events | Shallow | Intermediate | Deep | Tectonic reference |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Japan and Kuril | Northern Tohoku / Japan Trench | 351 | 309 | 21 | 21 | [USGS](https://pubs.usgs.gov/of/2010/1083/d/) |
| Indonesia and Philippines | East Java / Sunda-Java Trench | 59 | 35 | 16 | 8 | [USGS](https://www.usgs.gov/publications/seismicity-earth-1900-2012-java-and-vicinity) |
| Tonga Kermadec Fiji | Central Tonga / Tonga Trench | 640 | 369 | 85 | 186 | [USGS](https://pubs.usgs.gov/of/2010/1083/i/) |
| Andes | Northern Chile / Peru-Chile Trench | 185 | 51 | 131 | 3 | [USGS](https://pubs.usgs.gov/of/2015/1031/e/) |
| Alaska and Aleutians | Central Aleutians / Aleutian Trench | 129 | 118 | 11 | 0 | [USGS](https://www.usgs.gov/publications/seismicity-earth-1900-2010-aleutian-arc-and-vicinity) |
| Mediterranean and Himalaya | Western Crete / Hellenic Arc | 57 | 52 | 5 | 0 | [USGS](https://pubs.usgs.gov/of/2010/1083/q/) |
| Other | Southern Hikurangi, New Zealand / Local example | 73 | 58 | 15 | 0 | [USGS](https://www.usgs.gov/publications/upper-plate-heterogeneity-along-southern-hikurangi-margin-new-zealand) |

Endpoint locations appear below each map and section in the dashboard, including geographic descriptions and coordinates. OpenStreetMap reverse geocoding was used to check the Japan and northern Chile land endpoints.

Route review used rendered point clouds, mapped coverage, sample sizes and 50/100/200 km half-width checks. The following changes were retained.

- Japan changed from the 38 N east-west trial to a west-northwest route through northern Tohoku. The trial had 617 events, including nine intermediate and three deep events. The selected route has 351 events, including 21 intermediate and 21 deep events, spread along the distance coordinate.
- Java compared meridional routes at 110 E, 112.5 E and 114 E, then a north-northeast East Java route. The meridional 112.5 E trial had deep-event counts of 1/12/15 at 50/100/200 km half-widths. The retained oblique route has 5/8/13, with total counts 41/59/128. Its angle to the local PB2002 boundary is approximately 79 degrees, compared with 75 degrees for the meridional trial.
- The Hellenic Arc compared 22.5 E, 24 E, 25.5 E and an oblique crossing. The selected 24 E line crosses western Crete. It has 57 events, including five intermediate events, compared with 88 events and three intermediate events at 22.5 E.
- Aleutian trials at 174 W, 171 W and 168 W retained 174 W. Hikurangi trials at 41 S and 41.5 S retained 41 S. Tonga and northern Chile retained their reference orientations and use the shared trench-centred distance window.

| Local setting | Known events at 50 / 100 / 200 km half-width | Deep events at 50 / 100 / 200 km half-width |
| --- | --- | --- |
| Northern Tohoku / Japan Trench | 131 / 351 / 636 | 9 / 21 / 26 |
| East Java / Sunda-Java Trench | 41 / 59 / 128 | 5 / 8 / 13 |
| Central Tonga / Tonga Trench | 290 / 640 / 1182 | 87 / 186 / 336 |
| Northern Chile / Peru-Chile Trench | 116 / 185 / 347 | 3 / 3 / 12 |
| Central Aleutians / Aleutian Trench | 61 / 129 / 220 | 0 / 0 / 0 |
| Western Crete / Hellenic Arc | 31 / 57 / 168 | 0 / 0 / 0 |
| Southern Hikurangi, New Zealand / Local example | 19 / 73 / 105 | 0 / 0 / 0 |

Counts and depth fractions change with sampling width. The figures describe local catalogue distributions. A single section provides limited spatial coverage within each broad catalogue region.

## Default regional 3D presentation

The existing 3D hypocentres view continues to show known-depth events across the selected catalogue region. The local cross-section sampling strip does not define this view. The original deterministic time-order display cap of 8,000 points is retained; the note reports the plotted and selected event counts.

The east/north reference and axis limits use all known-depth events in the catalogue region. Changing year, magnitude or depth filters therefore preserves the positions, limits and aspect ratios. East/north coordinates retain the original equirectangular display approximation, including the existing date-line handling. They are not used for distance analysis; the approximation is particularly limited for the global Other group.

Horizontal axes use equal kilometre scales. Depth is displayed positive down, with geometric z equal to negative reported depth. To keep the depth dimension readable, its displayed span is at least half the larger horizontal span. The resulting vertical exaggeration, max(1, 0.5 × maximum horizontal span / depth span), is fixed within each region and stated below the chart. Apparent slopes must be interpreted with this factor.

The default view uses a fixed oblique orthographic camera, a horizontal legend, the original blue/orange/purple depth classes, smaller semi-transparent points and subdued grids. Scene sizing follows the desktop plot area. Hover cards retain event ID, depth, magnitude and class, without axis spikes. The view order and existing menus are unchanged.

Following the approved Japan trial, all seven regional groups use marker size 1.6 and opacity 0.8. This presentation change preserves every plotted event, coordinate, class colour, axis and camera setting.

## Japan depth-guide preview

Two dashed guides on the rear walls mark the 70 km and 300 km depth-class boundaries. These are classification guides, rather than geological layer surfaces. The trial coastline overlay was removed following visual review because it obscured the shallow-event pattern.

The preview adds an English region title, slightly different pale blue-grey wall and floor colours, and a larger scene with responsive spacing. Event coordinates, class colours, marker size, opacity, axis limits, camera direction and relative axis scales are preserved. Guide traces do not contribute to event counts, class legends or event hover cards. The other six regional groups retain their approved appearance.

## Verification of the three RQ3 tasks

The current acceptance scope is the original 03 Depth panel with the histogram, boxplots and class shares; seven route-map/local-section pairs; and seven regional 3D views. Local profile samples and full-region 3D samples intentionally have different scopes. The current build entry point is `run_pipeline.py --offline`.

Run `python -m pytest -q`, `python verify_results.py`, and `python scripts/verify_rq3.py` in the project environment. The last command independently recomputes catalogue partitions and shares, spherical trench intersections, along/cross-track distances, finite-strip event IDs, endpoints and width sensitivities without importing the production geometry helpers. Its receipt is `outputs/rq3_independent_verification.json`.

Run `node scripts/rq3_browser_acceptance.cjs` for focused interaction checks. It requires Playwright and a Chromium browser; `PLAYWRIGHT_MODULE` and `PLAYWRIGHT_CHROMIUM_EXECUTABLE` can select installed locations. The script checks all seven regions, real box hover cards, rendered quartiles, percentage denominators, missing/negative/boundary depths, map/profile event identity, equal profile scales, 3D coordinates and sampling, representative filters, empty states, and desktop layouts. Evidence is saved under `outputs/rq3_browser_acceptance/`.

The supported scope is the desktop browser. Phone-specific text measurement, wrapping, sizing and acceptance tests are omitted to keep the implementation concise. The original page's shared styles remain. Calculations, regional colours and the accepted desktop structure are unchanged. Verification uses the retained historical snapshot and Windows/Edge; it does not refresh USGS data, validate a slab model, or exhaust every possible filter combination.
