# Inside the Earth

**DSC5002 Exploratory Data Analysis and Visualization — earthquake project baseline.**

A reproducible Python implementation of the supplied project proposal, covering all five research questions with real USGS observations, spherical PB2002 boundary distances, twelve figures, a standalone interactive dashboard and an English results report. Team assignments are intentionally omitted.

## 快速使用

本地成品已生成，可以直接双击打开：

- `outputs/dashboard.html`：离线交互面板，包含全球地图、可旋转 3D 地球、区域深度剖面、3D 震源视图、筛选器和三场重大地震案例。
- `outputs/report.html`：英文结果报告，包含 12 张图、数据审计、五个研究问题的结果与解释边界。请保留整个 `outputs` 文件夹，报告需要读取旁边的图片。
- `data/processed/earthquakes.csv`：清洗及派生变量后的完整分析数据。
- `outputs/tables/`：统计表、Spearman 相关系数、案例事件列表与敏感性分析。

所有文件均位于 `5002final`。公开仓库包含代码、测试、文档、来源清单和一张面板预览；原始数据、生成结果和输入 Word 计划保存在本地，不加入 Git。克隆仓库后运行下列命令即可重新生成。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_pipeline.py
.\.venv\Scripts\python.exe verify_results.py
.\.venv\Scripts\python.exe -m pytest -q
Start-Process .\outputs\dashboard.html
```

Python **3.11 or 3.12** is required; the local baseline was checked with Python 3.12.3. No API key is required. The first run needs internet access to USGS and raw.githubusercontent.com. Subsequent runs can use the verified cache:

```powershell
python run_pipeline.py --offline
```

`--offline` makes no HTTP requests. Source downloads and the expensive distance calculation are reused only when their stored SHA256 hashes and relevant configuration/code bindings match. Browser use requires a modern browser with WebGL for the 3D views; the 2D views and report work without those views.

## Research scope

| Question | Implemented baseline |
| --- | --- |
| RQ1 Where and when? | Annual counts, regional count heatmap, global point map and rotatable globe |
| RQ2 Near plate boundaries? | Exact spherical nearest-segment distances, histogram and regional ECDFs |
| RQ3 Regional depth? | Depth classes, histograms, boxplots, longitude–depth projections and 3D hypocentres |
| RQ4 Magnitude and frequency? | 0.1-magnitude histogram, exact cumulative counts and descriptive correlations |
| RQ5 Major events? | Sumatra Andaman 2004, Maule 2010 and Tohoku 2011; fixed local maps and timelines |

The observation window is **[2000-01-01, 2026-01-01) UTC**, preferred magnitude **M ≥ 5**, event type **earthquake**. A saved count query and 26 annual CSV downloads reconcile to **46,463** unique events in this snapshot. Cleaning retains all of them. Downloads can change when USGS revises its catalogue; the saved manifest defines this local snapshot.

Selected baseline results are reported in [docs/BASELINE_RESULTS.md](docs/BASELINE_RESULTS.md). They describe the downloaded catalogue, not hazard forecasts or causal effects.

![Offline dashboard preview](docs/dashboard_preview.png)

## Data and methods

- [USGS Earthquake Catalog](https://earthquake.usgs.gov/fdsnws/event/1/) provides preferred event IDs, UTC time, latitude, longitude, depth, magnitude, magnitude type, place and review status. Annual requests avoid the 20,000-event response limit. The pipeline deduplicates IDs and applies the half-open study interval locally.
- [PB2002 GeoJSON conversion](https://github.com/fraxen/tectonicplates) provides 241 mapped boundary features. Every consecutive pair of vertices defines a minor great-circle arc. The distance algorithm tests on-arc perpendicular projections and endpoints on a sphere of radius 6371.0088 km. This is spherical geodesy, not an ellipsoidal estimate or a measure of geological uncertainty.
- [Natural Earth 110m](https://www.naturalearthdata.com/downloads/110m-physical-vectors/) supplies coastlines and land polygons, including the globe's land mask. Both geography repositories are pinned to commits in [data/sources.lock.json](data/sources.lock.json).

Regions are priority-ordered geographic boxes in `config.json`, with a catch-all **Other** category. Date-line crossing boxes are supported. Raw regional counts are not normalized by area. Depth classes are shallow **<70 km**, intermediate **70–<300 km**, and deep **≥300 km**. Missing depths remain in the cleaned dataset and are omitted only from analyses that require depth; negative recorded depths are retained and flagged.

Case anchors are the maximum-magnitude observations on the three predefined dates. Case samples use spherical epicentral distance ≤500 km and equal 30-day windows **[−30,0)** and **[0,30)** relative to the anchor's exact timestamp, excluding the anchor ID. Their dedicated dashboard tab uses the full M≥5 catalogue; it hides the global filters and explicitly states this independent scope.

Sensitivity tables vary regional boxes by ±2°, depth cutoffs and the case windows/radii. Spearman coefficients are descriptive and repeated by region and two equal 13-year periods. No independent-observation p-values, fitted predictive models or causal claims are reported. Globe, relationship and 3D hypocentre displays cap plotted points at 8,000 and disclose sampling; statistical summaries use every eligible event. Static figures use all available rows.

## Layout

```text
config.json                     Study window, geographic boxes and case definitions
run_pipeline.py                 Download → clean → distances → tables → figures → HTML
verify_results.py               Independent source/count/case/spatial/artifact checks
earthquake_explorer/             Acquisition, geometry, analysis and rendering modules
web/                            Embedded dashboard HTML/CSS/JavaScript source
tests/                          Small synthetic regression cases; no network required
scripts/                        Download-only, preparation-only and optional browser QA
data/sources.lock.json           Versioned URLs, access timestamps and source hashes
data/raw/                       Local verified raw CSV and geography files (Git-ignored)
data/processed/                  Local analysis dataset, audit and processing seal (ignored)
outputs/                        Local report, dashboard, figures, tables and QA receipts
local_sources/                   Local copy of the input DOCX (Git-ignored)
docs/                           Methods, limitations, baseline snapshot and preview
```

## Validation

```powershell
python -m pytest -q
python verify_results.py
```

`verify_results.py` rechecks source hashes, independently reconciles annual/depth/magnitude/case counts and validates 256 sampled distances against an independent PB2002 spherical-node oracle with ≤1 km node spacing. A node distance must upper-bound the arc distance by no more than 0.501 km; this numerical bound does not quantify map or geological uncertainty. It also verifies all generated artifact hashes.

Optional browser QA checks filters, the empty-result state, the globe, date-line sections, 3D hypocentres, exact case counts, mobile layout, report images and absence of HTTP requests. Install Playwright plus Chromium separately if desired, then run `node scripts/browser_smoke.cjs`. `PLAYWRIGHT_BROWSER_CHANNEL=msedge` allows an installed Edge browser. The project itself has no Node runtime requirement. The browser fixture intentionally checks the delivered 46,463-event baseline and must be updated if the observation scope or catalogue snapshot changes.

GitHub Actions runs the network-free regression suite on Python 3.11 and 3.12. CI does not pretend to validate a new USGS snapshot without downloading and checking it.

## Limits and remaining work

An M5 threshold does not prove uniform completeness. The catalogue mixes magnitude types, includes dependent event sequences and can be revised. PB2002 is simplified and dated. Regional boxes differ in size and composition. Cross-sections project all latitudes in a broad box and exaggerate vertical scale. The local 3D coordinate approximation is for display only. Results apply to recorded events in the selected window.

This baseline does not implement magnitude homogenization, completeness estimation, declustering, narrow trench-normal sections, formal hypothesis testing, causal identification, hazard prediction, a presentation deck or team allocation. The optional animation is deferred because static timelines already show the selected sequences.

Code is MIT-licensed; data and bundled runtime assets keep their own terms. See [THIRD_PARTY.md](THIRD_PARTY.md), [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) and [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).
