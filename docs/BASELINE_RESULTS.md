# Baseline results

Snapshot: 30 October 2026. Source scope: USGS earthquakes, M≥5, [2000-01-01, 2026-01-01) UTC. The saved source count and annual CSV batches reconcile to **46,463** unique events; all are retained after cleaning. There are no missing depths and four negative reported depths, which are retained and flagged.

| Descriptive statistic | Value |
| --- | ---: |
| Largest annual count | 2,701 in 2011 |
| Median preferred magnitude | 5.2 |
| Median depth | 23.70 km |
| Median spherical PB2002 boundary distance | 59.68 km |
| Within 50 km of a mapped boundary | 43.92% |
| Within 100 km of a mapped boundary | 70.15% |
| Within 250 km of a mapped boundary | 91.54% |
| Shallow events (<70 km) | 38,656 |
| Intermediate events (70–<300 km) | 6,083 |
| Deep events (≥300 km) | 1,724 |
| Events with M≥7 | 387 |
| Events with M≥8 | 28 |

The pooled pairwise Spearman coefficients are −0.0038 for magnitude/depth, 0.0155 for magnitude/boundary-distance, and 0.3868 for depth/boundary-distance. These are observational coefficients; sequence dependence and regional composition prevent a causal reading. Subgroup coefficients are saved by region and by two equal 13-year periods.

| Selected case | Anchor magnitude | Before | After |
| --- | ---: | ---: | ---: |
| Sumatra Andaman 2004 | 9.1 | 2 | 143 |
| Maule Chile 2010 | 8.8 | 1 | 302 |
| Tohoku Japan 2011 | 9.1 | 33 | 563 |

Each side has 30 days of exposure within a 500 km spherical epicentral radius. Windows are [−30,0) and [0,30) days; the anchor is excluded. All windows are fully observed. These selected comparisons exclude earthquakes below M5 and are not a general causal estimate.

The locally generated report links results to twelve figures and CSV tables. The dashboard includes filters, an offline globe and regional depth views. The numerical and rendered checks are summarized in [validation_snapshot.json](validation_snapshot.json).

Boundary distances are exact for the selected spherical segment model, with R=6371.0088 km. PB2002 is a dated, simplified map; spherical geometry and catalogue accuracy limit interpretation. An M5 threshold does not prove uniform completeness. Magnitude types have not been homogenized, and regional boxes differ in area and composition. No hazard forecast or causal claim is made.
