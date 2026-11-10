# Current four-column delivery validation

Validated on 2026-11-10 against the frozen 46,463-event catalogue.

| Current check | Result |
|---|---|
| Python regression suite | 30 passed |
| Independent extension audit | 164 checks passed; CDFs, threshold shares, magnitude proxy, correlations, all 27 case windows and 93 cumulative checkpoints |
| Reference-distance oracle | 640 reference points across all five designs; 282,503 spherical nodes with spacing ≤1 km; maximum upper-bound gap 0.164264 km, below the 0.501 km bound |
| PDF | One A0 landscape page, four columns, 13 figure groups, 6,177 extractable characters, five correctly placed source/repository links, no animation links |
| Presentation script | Two searchable pages, rendered and visually inspected |
| Static browser delivery | Four entry/report pages; all images and local links load, desktop/mobile fit, no page errors or external requests |
| Current exports | 14 scientific figures in PNG and vector PDF; all poster copies byte-identical; obsolete animation poster image removed |

Poppler renders of the whole poster and enlarged panels were inspected. Two clipped
legends were repaired; cross sections now use paired local route maps and equal-km
profiles; the CDF legend was moved off the curves. Presentation-note leading was
adjusted to avoid an orphan line on a third page. The final PDF retains searchable
body text, chart axes, captions and references.

Fresh independent review checked data, mathematical claims, cache provenance,
figure semantics and PDF links. Two substantive findings were repaired: sampling
settings/runtime versions now participate in the spatial-reference cache binding;
footer links now use text-aligned inline annotations. Packaging was also made
independent of unavailable team originals, with historical receipts included only
when present. The reference ratio is explicitly descriptive, not a seismicity
null-model test, causal effect or hazard multiplier.

Previously completed component audits remain applicable to unchanged inputs and
methods: 442 submission checks, 105 RQ3 geometry/selection checks, 4,425 temporal
checks and 29 RQ3 browser checks. These are inherited component evidence, not
newly rerun counts. All 98 submitted originals were hash-verified after relocation;
`others` was removed. Original inputs remain local. The only poster edition in
current deliverable/public paths is the latest four-column PDF; duplicate locations
are identical distribution copies.

The supplied all-type extract supports the 60 non-earthquake finding, but is not
proof of byte identity with Member 2's unavailable original download. Future USGS
revisions require a new validation and revised poster text. Public artifact hashes
are computed after LF normalization. Live deployment is verified after Git push.
Machine-readable receipts are in `docs/final_results`.
