"""Publish only current aggregate results; replace the former animation landing page."""
from pathlib import Path
import shutil,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final';PUB=ROOT/'docs/final_results';PUB.mkdir(exist_ok=True)
published=set()
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    if PUB in dst.parents:published.add(dst.resolve())
def write(path,text):
    path.write_text(text,encoding='utf-8')
    if PUB in path.parents:published.add(path.resolve())
names=['global_map','boundary_cdf','regional_proximity','annual','regional_change','magnitude_mix','depth_shares','cross_sections','correlations','magnitude','energy_scale','case_timelines','case_cumulative','window_sensitivity']
tables=['annual_counts','regional_summary','region_depth_counts','numeric_summary','spearman_correlations','magnitude_frequency','case_comparison','case_window_sensitivity','member3_region_summary','member3_section_summary','spatial_reference_cdf','spatial_reference_summary','case_cumulative','depth_distance_summary']
for name in tables:copy(OUT/'tables'/f'{name}.csv',PUB/'tables'/f'{name}.csv')
for name in names:
    for ext in ['pdf','png']:copy(OUT/'poster_charts'/f'{name}.{ext}',PUB/'poster_charts'/f'{name}.{ext}')
for sub in ['rq4/figures','rq4/tables']:
    for src in (OUT/sub).glob('*'):
        if src.is_file() and src.name!='largest_events.csv':copy(src,PUB/sub/src.name)
for name in ['poster_facts','expanded_facts','expansion_verification','pdf_verification','poster_layout_checks']:
    copy(OUT/f'{name}.json',PUB/f'{name}.json')
for source,destination in [('submission_audit.json','submission_audit.json'),('rq3_independent_verification.json','rq3_independent_verification.json'),('rq3_browser_acceptance/verification.json','rq3_browser_verification.json')]:
    if (OUT/source).exists():copy(OUT/source,PUB/destination)
if (OUT/'current_browser_verification.json').exists():copy(OUT/'current_browser_verification.json',PUB/'current_browser_verification.json')
for dst in [ROOT/'docs/poster.pdf',OUT/'poster.pdf']:copy(ROOT/'deliverables/DSC5002_Academic_Poster.pdf',dst)
copy(ROOT/'deliverables/DSC5002_Presentation_Script.pdf',ROOT/'docs/presentation_script.pdf')
copy(OUT/'poster_preview.png',ROOT/'deliverables/Poster_Preview.png')
copy(OUT/'poster_preview.png',ROOT/'docs/poster_preview.png')
write(ROOT/'docs/.nojekyll','')
REPO='https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer';SITE='https://victoriasu551.github.io/DSC5002-Earthquake-Explorer/'
css='''*{box-sizing:border-box}body{font:17px/1.65 system-ui,sans-serif;color:#123346;background:#f3f6f7;margin:0}main{max-width:1180px;margin:auto;padding:44px 28px}h1{font-size:clamp(36px,6vw,64px);line-height:1.06;letter-spacing:-1px;margin:.3em 0}h2{font-size:28px;margin:48px 0 16px}h3{font-size:21px;margin:0 0 10px}a{color:#146e8b;text-underline-offset:3px}figure{background:#fff;border-radius:10px;margin:18px 0 36px;padding:20px;box-shadow:0 4px 22px #12334608}img{width:100%;height:auto;display:block}figure img{max-height:650px;object-fit:contain}figcaption{margin-top:14px;font-size:16px;color:#405b6a}.lead{font-size:23px;max-width:900px}.note{background:#e4eef1;border-left:5px solid #197c9e;padding:20px;margin:24px 0}nav{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}nav a,.button{display:inline-block;background:#123346;color:white;padding:10px 18px;border-radius:5px;text-decoration:none}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:30px 0}.card{background:#fff;padding:22px;border-top:5px solid #197c9e;border-radius:5px}.card:nth-child(2){border-color:#c95d54}.card:nth-child(3){border-color:#8254a6}.card:nth-child(4){border-color:#d58c27}.card strong{display:block;font-size:34px;line-height:1.2}.eyebrow{text-transform:uppercase;letter-spacing:2px;color:#617582;font-size:13px}table{border-collapse:collapse;font-size:14px;width:100%}td,th{border-bottom:1px solid #d9e7ec;padding:8px;text-align:left}.table-wrap{overflow-x:auto;background:white;padding:14px}code{overflow-wrap:anywhere}footer{font-size:14px;border-top:1px solid #ccdbe1;padding:24px 0;margin-top:38px}@media(max-width:600px){main{padding:25px 16px}figure{padding:10px}figcaption{font-size:14px}}'''
def page(title,body,lang='en'):
    return f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body><main>{body}</main></body></html>'
panels=[
('global_map','01 · Space / Where are the recorded events?', 'All 46,463 epicentres on an equal-area Mollweide map. Blue: shallow (<70 km); gold: intermediate (70–<300 km); purple: deep (≥300 km). Coastlines and PB2002 boundaries provide context. Points overlap: colour darkness is not an estimated density or hazard rate.'),
('boundary_cdf','A geographic reference changes the question','At 100 km from PB2002, 70.15% of earthquakes are included, versus 9.42% of equal-area globe points and 10.50% of the latitude-controlled reference. The 7.45 ratio is a descriptive share ratio. Four scrambled Sobol designs of 16,384 points each give 9.38–9.53%; this range measures numerical sensitivity, not a confidence interval. All locations, including oceans, are eligible. Neither reference is a realistic seismicity null model.'),
('regional_proximity','The concentration is geographically uneven','Each dot is the percentage within 100 km using that region’s own earthquake denominator. Other combines many locations outside the six configured geographic boxes; its high share should not be read as a coherent tectonic-region effect. The model uses nearest minor great-circle arcs, not nearest stored vertices.'),
('annual','02 · Time / The catalogue fluctuates','The annual peak is 2,701 records in 2011. Comparing 2013–2025 with 2000–2012 gives a 6.63% lower M≥5 record rate and 15.42% lower M≥6 rate, adjusted for 4,748 versus 4,749 days. A positive full-period M5 Sen slope shows that a different summary can produce a different direction. These are catalogue descriptions, not a forecast.'),
('regional_change','A single global contrast conceals regional differences','Exposure-adjusted within-region changes range from −25.58% in Indonesia/Philippines to +8.82% in Mediterranean/Himalaya. All regions use identical periods. Unequal box areas and detection practices prevent interpreting raw regional counts as comparable hazard.'),
('magnitude_mix','The two periods are not measurement-equivalent','Mw-family share changes from 73.45% to 55.05%. Horizontal-error availability changes from 0.28% to 86.80%; missing error does not mean zero error. Preferred magnitude types, reporting fields and exact-depth concentrations vary through time. A Mw-only subset still does not homogenize magnitude measurement or prove completeness.'),
('depth_shares','03 · Depth / Similar medians can conceal different tails','83.20% of the catalogue is shallow. Japan/Kuril and Tonga/Kermadec/Fiji both have median depth 33 km, yet their deep-event shares are 5.01% and 11.76%. Andes has 26.19% intermediate-depth events. All records have reported depth; four negative depths remain in the shallow category.'),
('cross_sections','Two finite sections make local structure visible','Local maps show the PB2002 trench (gold), route and ±100 km swath (blue), and trench origin (star). Direction A→B spans −200 to +1,200 km from the trench. Depth plots use equal kilometre scales; no vertical exaggeration. Membership also requires the parent region. Deep observations number 21/351 in northern Tohoku and 186/640 in central Tonga. Routes were chosen after exploration and are illustrative, not independent tests of slab structure.'),
('correlations','Depth and boundary distance are associated','Spearman rank correlations use every eligible record in each displayed group. Depth–distance rho is +0.3868 globally and +0.5556 in Japan/Kuril. Magnitude–depth and magnitude–distance associations are generally weak, but pooled near-zero coefficients cannot exclude subgroup or nonlinear relationships. Correlations do not identify a causal mechanism; no independent-event p-values are reported.'),
('magnitude','04 · Magnitude / Large events are rare','The inclusive cumulative count N(M≥m) retains threshold ties: 3,874 observations at M≥6, 387 at M≥7, 28 at M≥8, and two at M≥9. The count axis is logarithmic. The M5 extraction threshold does not establish catalogue completeness, so no predictive Gutenberg–Richter b-value is fitted.'),
('energy_scale','Frequency and a magnitude-based proxy tell different stories','The dimensionless illustrative proxy R(M)=10^(1.5(M−5)) scales by about 31.6 for a one-unit magnitude increase. M≥8 represents 0.0603% of events but 71.2144% of its summed value. Preferred scales are mixed: these are not measured joules, damage estimates or risk. The sum is dominated by rare extreme events.'),
('case_timelines','Selected sequences on identical axes','Sumatra 2004, Maule 2010 and Tohoku 2011 use ≤500 km epicentral radius and UTC windows [−30,0) and [0,30) days relative to the exact anchor timestamp. The anchor is excluded. Before/after counts are 2/143, 1/302 and 33/563. Identical y-axis ranges preserve comparability; no offset is hidden behind a logarithmic axis.'),
('case_cumulative','Timing separated from total counts','Each curve is normalized by its own 30-day post-window total. The first three days contain 60.1%, 60.9% and 70.9% of the respective post-window records. The day-d value counts events in [0,d); all curves reach 100% at day 30. These time-and-distance selections do not establish causal aftershock membership.'),
('window_sensitivity','Supplement / Window choices materially change counts','Each cell is the post-window count at the indicated duration (7, 30 or 90 days) and radius (250, 500 or 1,000 km), excluding the anchor. All 27 windows are fully observed. A common colour range and printed counts support comparison. These nested samples are sensitivity checks, not independent replicates.')]
body='<p class="eyebrow">DSC5002 · Current integrated results</p><h1>Inside the Earth</h1><p class="lead">Four connected views of global earthquakes: space, time, depth and magnitude.</p><nav><a href="@POSTER@">Searchable academic poster</a><a href="@SCRIPT@">Presentation script</a><a href="@TEMPORAL@">Temporal-comparability supplement</a></nav>'
body+='<h2>Research design</h2><p>One frozen USGS earthquake-only snapshot links all five research questions: 46,463 unique events in [2000-01-01, 2026-01-01) UTC with preferred M≥5. Six priority-ordered geographic boxes plus Other partition the catalogue. Source requests, input hashes and reproducible calculations are retained. Geographic distances use PB2002 minor great-circle arcs on a sphere of radius 6,371.0088 km.</p><div class="note"><b>Extension from proposal 2.0:</b> explicit equal-area and latitude-controlled spatial references; region-stratified associations; event shares versus an illustrative energy scale; normalized cumulative case curves; and radius/time sensitivity. Static panels were selected to answer these questions directly.</div>'
for i,(name,title,caption) in enumerate(panels,1):
    body+=f'<h2>{title}</h2><figure><img src="poster_charts/{name}.png" alt="{title}" loading="lazy"><figcaption>{caption} <a href="poster_charts/{name}.pdf">Vector PDF</a></figcaption></figure>'
    if name=='boundary_cdf':body+='<div class="table-wrap">'+pd.read_csv(OUT/'tables/spatial_reference_summary.csv').round(3).to_html(index=False,border=0)+'</div>'
body+='<h2>Interpretation and sensitivity</h2><p>Removing the union of 30-day / 500 km windows around all 28 M≥8 anchors removes 3,090 unique records (including anchors) and changes the M5 period contrast to −3.37%. This is a window-removal sensitivity, not a declustered catalogue. Geographic boxes, threshold choices, changing reporting and selected case windows all affect the comparisons. The strongest defensible conclusions are descriptive: boundary concentration relative to geographic references, contrasting depth tails, rare large magnitudes, and temporally clustered selected sequences.</p>'
body+='<h2>Review, provenance and reproducibility</h2><p>Member 2’s event-type and distance choices required correction. The supplied all-type data contain 55 volcanic eruptions, four nuclear explosions and one landslide; excluding them reconciles the 46,463 earthquakes. Member 3 section methods and Member 4 magnitude calculations were adopted after numerical review. Raw submissions remain local audit material. See <a href="@REVIEW@">team review</a> and <a href="@EXTENSION@">extension methods</a>.</p><p>Canonical SHA256: <code>231b5b4fadf2d0d4eccfe4f03b8eb8489d225ff84e921f18d2b973af46d544ff</code>.</p>'
body+=f'<footer><a href="https://earthquake.usgs.gov/fdsnws/event/1/">USGS FDSN</a> · <a href="https://doi.org/10.1029/2001GC000252">Bird (2003), PB2002</a> · <a href="https://github.com/fraxen/tectonicplates">GeoJSON conversion (ODC-By)</a> · <a href="https://www.naturalearthdata.com/">Natural Earth (public domain)</a> · <a href="https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity">USGS magnitude–energy guidance</a> · <a href="{REPO}">Code and all results</a></footer>'
for target,mapping in [(OUT/'report.html',{'POSTER':'poster.pdf','SCRIPT':'../../deliverables/DSC5002_Presentation_Script.pdf','TEMPORAL':'../temporal_regional_v2_20261103/report.html','REVIEW':'../../docs/TEAM_REVIEW.md','EXTENSION':'../../docs/EXPERIMENT_EXTENSION.md'}),(PUB/'report.html',{'POSTER':'../poster.pdf','SCRIPT':'../presentation_script.pdf','TEMPORAL':'../temporal_regional_v2/report.html','REVIEW':'../TEAM_REVIEW.md','EXTENSION':'../EXPERIMENT_EXTENSION.md'})]:
    result=body
    for k,v in mapping.items():result=result.replace('@'+k+'@',v)
    write(target,page('Inside the Earth | Current results',result))
cards='<div class="cards"><div class="card"><strong>46,463</strong>Earthquake records, 2000–2025</div><div class="card"><strong>7.45×</strong>100-km share / equal-area reference</div><div class="card"><strong>11.76%</strong>Deep-event share, Tonga / Fiji</div><div class="card"><strong>28</strong>Events at magnitude ≥8</div></div>'
landing='<p class="eyebrow">City University of Hong Kong · DSC5002</p><h1>Inside the Earth</h1><p class="lead">Global earthquake patterns across space, time, depth and magnitude.</p>'+cards+'<nav><a href="poster.pdf">Download poster PDF</a><a href="final_results/report.html">Explore all 14 figures</a><a href="presentation_script.pdf">Presentation script</a></nav><figure><a href="poster.pdf"><img src="poster_preview.png" alt="Current five-column academic poster"></a><figcaption>Current edition: five evidence columns, six searchable data tables, five selected figures and explanatory prose. The supplementary report includes the window-sensitivity grid.</figcaption></figure><h2>What the new comparisons show</h2><p>70.15% of recorded earthquakes lie within 100 km of a mapped PB2002 boundary, versus 9.42% for equal-area globe points. This descriptive reference clarifies spatial concentration. Time trends are read alongside catalogue-comparability evidence; depth sections and stratified correlations reveal regional differences; cumulative case curves separate timing from totals.</p><p>All results describe a fixed catalogue. They do not estimate future hazard or establish causality.</p><footer><a href="EXPERIMENT_EXTENSION.md">Extension methods</a> · <a href="FINAL_VALIDATION.md">Validation</a> · <a href="'+REPO+'">GitHub repository</a></footer>'
write(ROOT/'docs/index.html',page('Inside the Earth | Academic poster and results',landing))
entry='<p class="eyebrow">DSC5002 · 最新成果入口</p><h1>Inside the Earth</h1><p class="lead">根据 2.0 扩充实验、重新设计的五列学术海报</p><nav><a href="deliverables/DSC5002_Academic_Poster.pdf">学术海报 PDF</a><a href="deliverables/DSC5002_Presentation_Script.pdf">展示讲稿 PDF</a><a href="outputs/final/report.html">完整结果与 14 组图</a><a href="outputs/final/dashboard.html">交互分析工具</a></nav><figure><img src="deliverables/Poster_Preview.png" alt="最新版五列海报预览"></figure><p>只以这里链接的最新版作为交付。原始数据与组员投稿保留作复核依据；旧海报和旧海报动画截图已移除。</p><p><a href="docs/EXPERIMENT_EXTENSION.md">2.0 与 3.0 的整合说明</a> · <a href="docs/TEAM_REVIEW.md">组员成果评审</a> · <a href="docs/FINAL_VALIDATION.md">验证记录</a> · <a href="'+SITE+'">在线成果</a></p>'
write(ROOT/'START_HERE.html',page('DSC5002 | 最新成果入口',entry,'zh-CN'))
write(PUB/'RESULTS.md','''# 最新五列海报与扩充实验

- [在线成果入口](https://victoriasu551.github.io/DSC5002-Earthquake-Explorer/)
- [可搜索海报 PDF](../poster.pdf)：A0 横版、五列、6 张表格与 5 组精选图。
- [完整报告](report.html)：14 组图，包含事件窗口敏感性补充图。
- [英文讲稿 PDF](../presentation_script.pdf)
- [2.0 / 3.0 整合与复现说明](../EXPERIMENT_EXTENSION.md)

固定 46,463 条 M≥5 地震记录。100 km 内占比 70.15%，等面积空间参照为
9.42%，纬度控制为 10.50%；比值 7.45 为描述性占比比值，不是风险倍数。
最新海报不用动画链接；静态时间线与累计曲线直接展示事件序列。
本目录只发布当前汇总图、表和验证记录，完整原始数据和投稿留在本地。
''')
# The publication directory is generated only. Remove obsolete exports deliberately.
for p in list(PUB.rglob('*')):
    if p.is_file() and p.resolve() not in published and p.name!='artifact_manifest.json':
        assert p.resolve().is_relative_to(PUB.resolve());p.unlink()
for p in [*PUB.rglob('*'),ROOT/'docs/index.html']:
    if p.is_file() and p.suffix in {'.json','.csv','.html','.md','.svg'}:
        content=p.read_bytes().replace(b'\r\n',b'\n')
        if p.suffix=='.svg':content=b'\n'.join(line.rstrip() for line in content.split(b'\n'))
        p.write_bytes(content)
manifest=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(PUB.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json']
(PUB/'artifact_manifest.json').write_bytes(json.dumps(manifest,indent=2).encode())
print(f'Packaged {len(manifest)} current public artifacts and replaced poster/report entry points.')
