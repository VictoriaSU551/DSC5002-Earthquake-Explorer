# Current five-column poster validation

Validated on 2026-11-10 against the frozen 46,463-event catalogue.

The current edition combines an abstract, research motivation, methods, findings,
interpretation and limitations with six searchable tables and five selected figures.
It replaces the former chart-dominated poster. The full report retains fourteen
analytical figures; those are complementary evidence, not alternate poster editions.

| Current presentation check | Result |
|---|---|
| PDF geometry | One A0 landscape page, 1189 × 841 mm, five columns |
| Searchable content | 7,444 extracted characters; all six tables and five figure captions searchable |
| Allocation checks | No overlap among paragraph, table or figure blocks; all allocations inside the page |
| Numerical review | All six tables and their rounding checked against source summaries; denominators and claims agree |
| Typography and layout | Poppler full-page and enlarged inspections; selected chart labels enlarged for the narrower columns |
| Independent glyph audit | Zero out-of-page glyphs in the final poster and section figure; the final Tonga tick is fully visible |
| Links | Five source/repository links aligned with their visible text; no animation links |
| Presentation script | Two searchable pages, with signposting matching all five columns and the current table/figure numbers |
| Browser delivery | Local/public entry pages and full reports checked on desktop and mobile; fourteen report images load |

The cross-section right margin was expanded after independent review found the last
Tonga tick label clipping. It now ends at 461.93 pt within a 475.2 pt figure page.
Table 1 explicitly labels shallow, intermediate and deep bands; qualitative cells
are left-aligned and numerical comparisons right-aligned. Header colours follow
column themes, with light alternating row shading and dedicated interpretation boxes.

The data and analytical definitions were not changed for this layout revision.
Previously validated analysis evidence remains: 30 regression tests, 164 independent
extension checks, 640 reference distances compared with a ≤1 km dense-node oracle
(maximum gap 0.164264 km, below the 0.501 km bound), 442 submission checks,
105 RQ3 checks, 4,425 temporal checks and 29 RQ3 browser checks. These counts distinguish
analytical validation from the new layout and table review.

All three distributed poster copies are identical and contain only the current
edition. Old posters are overwritten. Source data and the 98 reviewed submissions
remain local, with `others` removed. Generated public artifacts use LF-normalized
hashes. Live deployment is checked after pushing the current commit; local receipts
are stored in outputs/final. Machine-readable PDF/layout and public-artifact receipts
are published in docs/final_results.
