# Current five-column poster validation

Validated on 2026-11-10 against the frozen 46,463-event catalogue.

The current edition combines an abstract, research motivation, methods, findings,
interpretation and limitations with eight searchable tables and nine selected figures.
It uses measured-height flow to replace large fixed vertical allocations. The full report retains fourteen
analytical figures; those are complementary evidence, not alternate poster editions.

| Current presentation check | Result |
|---|---|
| PDF geometry | One A0 landscape page, 1189 × 841 mm, five columns |
| Searchable content | 11,956 extracted characters; all eight tables and nine figure captions searchable |
| Allocation checks | No overlap among paragraph, table or figure blocks; all allocations inside the page |
| Numerical review | All eight tables and their rounding checked against source summaries; denominators and claims agree |
| Typography and layout | Poppler full-page and enlarged inspections; selected chart labels enlarged for the narrower columns |
| Density and reading order | Each column follows question, comparison, result and interpretation; content blocks occupy 88.6–94.1% of the available body height |
| Links | Five source/repository links aligned with their visible text; no animation links |
| Presentation script | Two searchable pages, with signposting matching all five columns and the current table/figure numbers |
| Browser delivery | Local/public entry pages and full reports checked on desktop and mobile; fourteen report images load |

Figures preserve their natural aspect ratios and trim external whitespace. The cross-section
right margin retains room for the final Tonga tick label. Tight cropping was inspected
in the rebuilt figures and final poster; it does not change the equal-kilometre axes.
Table 1 explicitly labels shallow, intermediate and deep bands; qualitative cells
are left-aligned and numerical comparisons right-aligned. Header colours follow
column themes, with light alternating row shading and dedicated interpretation boxes.

Paragraph/heading gaps are approximately 2–3 mm, with 10 mm column gutters. The height
shares above measure allocated content blocks, not the proportion of coloured pixels.
All columns end between 762.8 and 787.7 mm; the conclusion starts at 799 mm. Full-page
Poppler inspection confirms the tighter layout, visible captions and separation of
body content, interpretation boxes and conclusion. The two script pages were also rendered
and checked for matching numbering and clean pagination.

The frozen input and existing analytical definitions remain unchanged. The new
magnitude-threshold proximity check is independently recomputed: M≥5/6/7 samples
contain 46,463 / 3,874 / 387 events, with 70.15% / 65.93% / 63.57% within 100 km.
The new duration table extracts existing 500 km sensitivity results for 7/30/90 days;
these nested samples are explicitly not independent replicates.

Current extension verification passes 167 checks, including the three new threshold
comparisons and 640 reference distances compared with a ≤1 km dense-node oracle
(maximum gap 0.164264 km, below the 0.501 km bound). Separately, 442 submission checks,
105 RQ3 checks, 4,425 temporal checks and 29 RQ3 browser checks were previously validated.
These historical counts distinguish prior analysis audits from the new layout and
table review. All 30 regression tests pass in the current run.

Independent read-only review found no critical or important issues. It recomputed
Table 3 from the sealed catalogue and Table 8 with separate haversine/UTC calculations,
checked script references and found no out-of-page glyphs. A minor formula-spacing
finding was corrected by moving the raised exponent to the first line of its paragraph.

All three distributed poster copies are identical and contain only the current
edition. Old posters are overwritten. Source data and the 98 reviewed submissions
remain local, with `others` removed. Generated public artifacts use LF-normalized
hashes. Live deployment is checked after pushing the current commit; local receipts
are stored in outputs/final. Machine-readable PDF/layout and public-artifact receipts
are published in docs/final_results.
