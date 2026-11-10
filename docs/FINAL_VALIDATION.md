# Final integration validation

Validated on 2026-11-10 against the frozen 46,463-event catalogue.

| Check | Result |
|---|---|
| Python regression suite | 27 passed |
| Team submission reconciliation | 442/442 passed |
| Independent RQ3 geometry/selection audit | 105/105 passed |
| Previous temporal analysis independent audit | 4,425 passed; original 30 outputs unchanged |
| RQ3 desktop browser acceptance | 29 checks passed, zero page errors, zero external requests |
| Final animation integration | All four frame counts, map aspect, trailing window, play/reset, mobile overflow and integrated section view passed |
| PDF | One A0 landscape page, 4,713 extractable text characters, nine figure captions, two animation URI links and three source links |
| Presentation script | Two searchable pages, rendered and visually inspected |
| Original submissions | All 98 submitted files SHA256-verified after relocation; empty others removed |

The fresh independent reviewer identified one important issue: animation maps
stretched geographic ranges to a wide panel. A browser regression failed with
an actual degree-scale ratio 0.6364 versus expected 1.00166, then passed after
locking y/x scales at each anchor latitude. The same correction was applied to
the single-case map. Keyframes and poster were regenerated. The document's
Chinese description of minor great-circle arcs was corrected as well.

Review scope deliberately excludes an unavailable Member 2 raw download: its
unfiltered query and the supplied all-type extract support the contamination
finding, but are not evidence of byte identity between members' downloads.
Future USGS revisions are a different snapshot and require revalidation.
Deployment and live links are checked separately after publishing.

Machine-readable receipts are in docs/final_results. Raw submitted files and
the complete frozen dataset remain local. Public artifact hashes are calculated
after LF normalization so they survive Git checkout unchanged.
