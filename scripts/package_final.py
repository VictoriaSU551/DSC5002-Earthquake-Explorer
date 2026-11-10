"""Prepare the final local entry page and a deliberate public-results allowlist."""
from pathlib import Path
import shutil,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final';PUB=ROOT/'docs/final_results';PUB.mkdir(exist_ok=True)
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
tables=['annual_counts.csv','regional_summary.csv','region_depth_counts.csv','numeric_summary.csv','spearman_correlations.csv','magnitude_frequency.csv','case_comparison.csv','case_window_sensitivity.csv','member3_region_summary.csv','member3_section_summary.csv']
for name in tables:
    src=OUT/'tables'/name
    if src.exists():copy(src,PUB/'tables'/name)
for sub in ['poster_charts','rq4/figures','rq4/tables']:
    for src in (OUT/sub).glob('*'):
        if src.is_file() and src.name!='largest_events.csv':copy(src,PUB/sub/src.name)
for name in ['poster_facts.json','submission_audit.json','rq3_independent_verification.json','browser_verification.json','pdf_verification.json','poster_layout_checks.json','animation_poster_keyframe.png']:
    copy(OUT/name,PUB/name)
copy(OUT/'rq3_browser_acceptance/verification.json',PUB/'rq3_browser_verification.json')
copy(OUT/'animation.html',ROOT/'docs/index.html')
copy(ROOT/'deliverables/DSC5002_Academic_Poster.pdf',ROOT/'docs/poster.pdf')
copy(ROOT/'deliverables/DSC5002_Academic_Poster.pdf',OUT/'poster.pdf')
copy(OUT/'poster_preview.png',ROOT/'deliverables/Poster_Preview.png')
(ROOT/'docs/.nojekyll').write_text('',encoding='utf-8')
facts=json.loads((OUT/'poster_facts.json').read_text())
css='body{font:17px/1.65 system-ui,sans-serif;color:#16364b;background:#f4f7f8;margin:0}main{max-width:1120px;margin:auto;padding:40px}h1{font-size:44px;line-height:1.15}h2{border-bottom:2px solid #d9e7ec;padding-bottom:8px;margin-top:48px}a{color:#167d8d}figure,table{background:white;margin:24px 0;padding:16px}img{max-width:100%}table{border-collapse:collapse;font-size:14px;width:100%}td,th{border-bottom:1px solid #d9e7ec;padding:7px;text-align:left}.lead{font-size:23px}.note{background:#e7f0f4;padding:18px}figcaption{font-size:15px}nav{display:flex;gap:20px;flex-wrap:wrap}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}.card{display:block;background:white;padding:20px;text-decoration:none;border-top:4px solid #167d8d}.card strong{display:block;font-size:23px}'
captions={
'global_map':('RQ1 / RQ2: Global geography','All 46,463 epicentres, coloured by depth; PB2002 and Natural Earth provide geographic context. No detection-completeness or area-normalized hazard claim.'),
'boundary_cdf':('RQ2: Boundary proximity','Shortest spherical distance to minor great-circle boundary arcs, R=6371.0088 km. Global and two selected regional ECDFs use their own denominators. Curves continue beyond the displayed 500 km range; no clipping of values to the endpoint.'),
'annual':('RQ1: Annual variation','Raw annual counts and calendar-year period means. Exposure-adjusted late-versus-early rates are -6.63% at M≥5 and -15.42% at M≥6. The positive full-period M5 Sen slope illustrates sensitivity to the chosen summary.'),
'regional_change':('RQ1: Regional comparisons','2013–2025 versus 2000–2012, rate per equal duration; regions are six configured boxes plus Other. Raw counts are not comparable hazard rates across unequal areas.'),
'depth_shares':('RQ3: Regional depth composition','Known-depth denominators; shallow <70 km, intermediate 70–<300 km, deep ≥300 km. All records have depth. Four negative reported depths remain in the shallow class.'),
'cross_sections':('RQ3: Two local cross sections','Adopted Member 3 methods: finite -200 to +1200 km route, ±100 km swath, parent-region restriction, spherical trench intersection. Distance and depth use equal scales. Profiles were explored and selected for illustration; their shapes are not an independent test of slab structure.'),
'magnitude':('RQ4: Magnitude and frequency','The histogram uses 0.1 magnitude bins; cumulative N(M≥m) includes threshold ties. Counts decrease across thresholds, with 3,874 records ≥6, 387 ≥7, 28 ≥8 and two ≥9. Mixed preferred magnitude types are not converted into a homogeneous Mw scale.'),
'case_timelines':('RQ5: Three selected major events','UTC offsets relative to each largest-on-date anchor. Windows [-30,0) and [0,30) days, distance ≤500 km, anchor excluded. All are fully observed; no causal aftershock classification.')}
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Inside the Earth | Integrated results</title><style>'+css+'</style><main><h1>Inside the Earth</h1><p class="lead">Integrated evidence across space, time, depth and magnitude</p><p>DSC5002 project · fixed 2000–2025 USGS catalogue · preferred M ≥ 5 · 46,463 unique earthquakes</p><nav><a href="../../deliverables/DSC5002_Academic_Poster.pdf">Academic poster</a><a href="animation.html">Interactive animation</a><a href="dashboard.html">Complete integrated dashboard</a><a href="../temporal_regional_v2_20261103/report.html">Full temporal-comparability report</a></nav>',
'<h2>Research design and contribution</h2><p>The project follows the five research questions in the supplied proposal. A single, sealed earthquake-only snapshot links descriptive statistics, maps, boundary distances, regional depth sections, magnitude-frequency curves and fixed-window event sequences. All substantive results below can be traced to the supplied tables and reproducible code.</p>',
'<div class="note"><b>Review decision:</b> Member 2 required correction of event-type filtering, region scope and boundary approximation. Member 3 depth methods, Member 4 magnitude calculations and RQ5 case metrics were adopted after numerical checks. The supplied all-type extract contains 55 volcanic eruptions, four nuclear explosions and one landslide; those 60 are excluded. It does not demonstrate a 60-earthquake catalogue revision.</div>',
'<h2>Data and processing</h2><p>UTC interval [2000-01-01,2026-01-01); event type earthquake; magnitude at least 5. Source requests and hashes are preserved. All 46,463 event IDs are unique. Coordinates, magnitude and depth are present; extreme or negative depths were not removed mechanically. Geometry uses PB2002 and Natural Earth 110m. Complete requested files do not establish detection completeness.</p>',
'<p>Canonical data SHA256: <code>'+facts['data_sha256']+'</code>. The original 30 baseline outputs remain unchanged. The final integration is a separate output version.</p>']
for name,(title,caption) in captions.items():
    parts+=['<h2>'+title+'</h2><figure><img src="poster_charts/'+name+'.png" alt="'+title+'"><figcaption>'+caption+'</figcaption></figure>']
    if name=='boundary_cdf':parts+=['<p>Median 59.68 km; 70.15% within 100 km; '+f"{facts['within_200km_pct']:.2f}"+'% within 200 km. The layer is dated and simplified; proximity is not geological uncertainty or a causal estimate.</p>']
    if name=='depth_shares':parts+=[pd.read_csv(OUT/'tables/member3_region_summary.csv').to_html(index=False,border=0)]
    if name=='cross_sections':parts+=[pd.read_csv(OUT/'tables/member3_section_summary.csv').to_html(index=False,border=0),'<p>Route maps, endpoint coordinates, seven profiles and regional 3D views are available in the integrated dashboard. The regional 3D view uses a documented display approximation and vertical exaggeration; display sampling does not alter table counts.</p>']
    if name=='case_timelines':parts+=[pd.read_csv(OUT/'tables/case_comparison.csv')[['name','before_count','after_count','peak_after_day','peak_day_count','first3_days_share_pct','largest_post_window_magnitude']].round(3).to_html(index=False,border=0),'<p><a href="animation.html"><b>Play the animation</b></a></p><figure><a href="animation.html"><img src="animation_poster_keyframe.png" alt="Actual cumulative animation at day three"></a><figcaption>Three synchronized cases at +3 days. Revealed totals include the before-window observations: 88/145, 185/303 and 432/596. The anchor is excluded; its star is a reference location at every frame. Maps preserve approximate kilometre aspect at each anchor latitude.</figcaption></figure>']
parts+=['<h2>Comparability and sensitivity</h2><p>We compare 13 calendar years against 13 calendar years with 4,749 and 4,748 days of exposure. Mw-family composition changes from 73.45% to 55.05%; error-field availability and concentrations at exact depths change too. These signals limit a direct interpretation as changing physical activity. The M≥5 sample cannot establish completeness below M5.</p><p>All 28 M≥8 anchors define a sensitivity union of 30-day, 500 km windows including those anchors. Removing 3,090 unique observations changes the M5 rate contrast to -3.37%. This is a window-removal sensitivity, not a declustered catalogue. See the full temporal report for threshold, review-status, region-box and annual-slope sensitivity results.</p>',
'<h2>Magnitude-type and illustrative energy supplement</h2>']
for name in ['rq4_03_magnitude_type_sensitivity','rq4_04_relative_energy_scale']:
    parts+=['<figure><img src="rq4/figures/'+name+'.png" alt="'+name+'"></figure>']
parts+=['<p>The 1.5-exponent relative proxy is dimensionless and uses mixed magnitude scales. Its summed shares are dominated by extreme events; they are not measured energy in joules, damage or hazard.</p><h2>Association and uncertainty</h2><p>Pooled Spearman rho is -0.00377 for magnitude/depth and 0.01552 for magnitude/boundary distance. Near-zero pooled monotonic association does not rule out subgroup relationships. The supplied correlations table includes region and period strata. No independent-event p-values or causal claims are inferred from clustered seismic sequences.</p><h2>Conclusion</h2><p>Recorded events concentrate near mapped boundaries, regional depth distributions differ markedly, larger magnitudes are rarer, and selected large-event windows exhibit strongly concentrated post-window counts. Catalogue composition, selected windows, geographic definitions and simplified geometry remain essential to interpretation.</p><h2>Sources and acknowledgements</h2><p><a href="https://earthquake.usgs.gov/fdsnws/event/1/">USGS FDSN catalogue</a>; <a href="https://doi.org/10.1029/2001GC000252">Bird (2003), PB2002</a>; <a href="https://github.com/fraxen/tectonicplates">GeoJSON conversion by Hugo Ahlenius (ODC-By)</a>; <a href="https://www.naturalearthdata.com/">Natural Earth</a> (public domain). RQ3 adapted from Member 3; RQ4 adapted from HUANG Youkun; case animation adapted from the RQ5 contributor. Full names not supplied are not invented.</p></main></html>']
html=''.join(parts);(OUT/'report.html').write_text(html,encoding='utf-8')
public=html.replace('href="animation.html"','href="../index.html"').replace('href="dashboard.html"','href="https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer#最终整合与学术海报2026-11-10"').replace('../temporal_regional_v2_20261103/report.html','../temporal_regional_v2/report.html')
(PUB/'report.html').write_text(public,encoding='utf-8')
(PUB/'RESULTS.md').write_text('''# 最终整合结果

- [学术海报 PDF](../../deliverables/DSC5002_Academic_Poster.pdf)
- [完整整合报告](report.html)（下载后可离线打开，或使用 GitHub Pages 同路径）
- [在线动画](https://VictoriaSU551.github.io/DSC5002-Earthquake-Explorer/)
- [组员成果评审](../TEAM_REVIEW.md)
- [讲稿 PDF](../../deliverables/DSC5002_Presentation_Script.pdf)

统一冻结目录：46,463 条 M≥5 地震，2000–2025 UTC。主要结论：70.15% 在
PB2002 边界 100 km 内；83.20% 为浅源；后十三年 M5 记录率低 6.63%；
Tonga/Kermadec/Fiji 深源占比 11.76%；M≥7 有 387 条，M≥8 有 28 条。
所有解释均为描述性，非预测或因果结论。

![海报预览](../../deliverables/Poster_Preview.png)

本目录只发布图、汇总表和验证结果。原始投稿和完整原始目录留在本地。
''',encoding='utf-8')
entry='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DSC5002 | 最终成果入口</title><style>'''+css+'''</style><main><h1>Inside the Earth</h1><p class="lead">DSC5002 最终整合成果 · 2026年11月10日</p><p>五个研究问题使用统一的 46,463 条地震记录。请优先使用下面的新版本。</p><div class="cards">
<a class="card" href="deliverables/DSC5002_Academic_Poster.pdf"><strong>学术海报</strong>A0 横版、可搜索 PDF，9 组图示及动画链接</a>
<a class="card" href="deliverables/DSC5002_Presentation_Script.pdf"><strong>展示讲稿</strong>约 6–7 分钟英文讲稿与常见问答</a>
<a class="card" href="outputs/final/report.html"><strong>完整整合报告</strong>五个研究问题、采用结果与方法限制</a>
<a class="card" href="outputs/final/dashboard.html"><strong>整合交互仪表盘</strong>全球地图、3D 地球、七组剖面、三案例动画；离线可用</a>
<a class="card" href="outputs/final/animation.html"><strong>独立动画</strong>三案例同步播放，累计/7天窗口模式</a>
<a class="card" href="outputs/temporal_regional_v2_20261103/dashboard.html"><strong>年度与地区比较</strong>时间、地区、震级门槛与数据可比性</a>
</div><h2>审核与复现</h2><ul><li><a href="docs/TEAM_REVIEW.md">组员成果评审与修改清单</a></li><li><a href="outputs/final/tables/">最终结果表</a></li><li><a href="outputs/final/rq4/figures/">震级分析完整补充图</a></li><li><a href="local_sources/team_submissions/">98 个原始投稿文件留档</a>（保留原稿，不代表最终采纳）</li></ul><p>旧版 outputs/dashboard.html 和 outputs/report.html 保留，避免覆盖已验证成果。新的统一入口即本页。</p><p><a href="https://VictoriaSU551.github.io/DSC5002-Earthquake-Explorer/">在线动画</a> · <a href="https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer">GitHub 仓库</a></p></main></html>'''
(ROOT/'START_HERE.html').write_text(entry,encoding='utf-8')
for p in [*(PUB.rglob('*')),ROOT/'docs/index.html']:
    if p.is_file() and p.suffix in {'.json','.csv','.html','.md','.svg'}:
        p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
manifest=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(PUB.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json']
(PUB/'artifact_manifest.json').write_bytes(json.dumps(manifest,indent=2).encode('utf-8'))
print(f'Packaged {len(manifest)} public results, local entry page, integrated reports and Pages files.')
