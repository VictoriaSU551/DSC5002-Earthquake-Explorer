# Annual and regional analysis

This extension uses the verified 30 October 2026 USGS snapshot: 46,463 earthquake events, M≥5, [2000-01-01, 2026-01-01) UTC. The analysis date is 3 November 2026. It never refreshes the catalogue or rewrites baseline inputs or outputs.

## Reproduce

```powershell
python run_temporal_analysis.py --publish
python verify_temporal_analysis.py
python -m pytest -q
```

A fresh clone first needs `python run_pipeline.py` to create a local baseline and processing seal. USGS revisions may change a newly downloaded catalogue; exact snapshot replay requires the original verified raw/processed cache and matching configuration/seal. The extension's read-only loader checks source hashes, configuration, preparation-code binding, dataset hash and event-ID grain. Missing or stale bindings stop the run without rebuilding. Keep a complete frozen snapshot together; byte hashes deliberately detect even changed manifest line endings.

## Measures

- Annual grids contain all 26 years, All plus seven geographic categories, and nested M≥5, 5.5, 6 and 7 thresholds. Zero cells remain zero; a year with no global events at a threshold has an undefined share.
- Periods are 2000–2012 and 2013–2025, both 13 calendar years but 4,749 versus 4,748 exposure days. Annual means divide by 13; exposure-standardized rates multiply N/days by 365.2425. Undefined zero-baseline ratios are blank in CSV and explicitly undefined in the tool. Period counts below 30 are flagged for ratio instability.
- Sen slopes are median distinct-year pairwise slopes. The range after omitting one year at a time is a descriptive sensitivity range, not a confidence interval. The centred three-year mean requires all three full years; endpoints are not extrapolated.
- Fixed priority-ordered region boxes match the baseline. Shares use each year's global count at the same threshold. Counts are not divided by region area or boundary length. Regional mean-count changes add exactly to the global mean-count change.
- Reporting metadata are joined from latest-update source records by stable event ID with a checked one-to-one join. Quality-field availability means finite and nonmissing, not zero uncertainty or validated accuracy. Raw magnitude tags are lower-cased for diagnostics only; no magnitude conversion is performed.
- Exact 10/33-km depth concentration is audited without assigning event-level fixed-depth flags. The `mw*` restricted subset is a selection sensitivity, not a homogenized catalogue. Review status and contributing-network mix are also tabulated.
- Window sensitivity removes the union of [anchor, anchor+30 days) within 500 km for every M≥8 preferred-catalogue anchor. Anchors are included, the date line is handled spherically, and overlapping windows count once. It is not formal declustering or a causal aftershock estimator.
- Additional comparisons vary boxes by ±2°, report reviewed-only/mw-prefix/window-excluded subsets at all thresholds, and compare multiyear blocks using correct exposure. The final block spans six years and must not be compared using raw totals alone.

## Interpretation

Matched extraction and exposure support comparisons of recorded catalogue counts. They do not establish identical detection completeness or magnitude/depth measurement. A sample truncated at M5 cannot by itself establish a completeness magnitude below that threshold. Event sequences are dependent. No naive event-level Poisson intervals, p-values, uniform-completeness assertion or physical hazard-change conclusion is used.

Official USGS documentation supports these interpretation limits. Source links appear next to the relevant report paragraphs and in the report's Sources section; the project statistics are calculated from the frozen inputs, not copied from web summaries.

## Outputs and checks

`outputs/temporal_regional_v2_20261103` contains fifteen local CSV/JSON tables, nine figures, report, interactive tool, provenance and artifact hashes. `docs/temporal_regional_v2` contains fourteen public aggregate tables/JSON plus the same figures and HTML deliverables. The local anchor-by-anchor sequence-window table stays outside Git.

`verify_temporal_analysis.py` independently checks counts, exact-day rates, shares, smoothing, Sen slopes/omitted-year ranges, raw metadata joins, reporting profiles, category mix, window unions, selection/box sensitivities, source partitions, published hashes and preservation of all baseline artifacts. The optional `scripts/temporal_browser_smoke.cjs` checks actual displayed counts, filtering, exposure, zero years, audit rows, images, local links, mobile layout and zero HTTP requests.

Published aggregate text assets use deterministic UTF-8/LF serialization. Git's CSV rule preserves their byte hashes across checkouts. Figure byte comparisons are demonstrated in the same pinned local environment; different font/rendering stacks may render PNGs differently.
