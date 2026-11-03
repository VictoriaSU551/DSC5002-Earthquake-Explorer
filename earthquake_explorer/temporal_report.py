"""Readable evidence-led report and an aggregate-only offline comparison tool."""
import json
from html import escape
from pathlib import Path
from plotly.offline import get_plotlyjs
from .report import table
from .dashboard import safe_json
from .temporal_figures import FIGURES
from .temporal_analysis import records

SOURCES=[
 ('USGS catalogue API','https://earthquake.usgs.gov/fdsnws/event/1/'),
 ('USGS catalogue fluctuations and detection','https://www.usgs.gov/faqs/why-are-we-having-so-many-or-so-few-earthquakes-has-naturally-occurring-earthquake-activity'),
 ('USGS magnitude types','https://www.usgs.gov/programs/earthquake-hazards/magnitude-types'),
 ('USGS depth reporting','https://www.usgs.gov/faqs/why-do-so-many-earthquakes-occur-a-depth-10km'),
 ('USGS magnitude revisions','https://www.usgs.gov/faqs/whywhen-does-usgs-update-magnitude-earthquake'),
 ('USGS source CSV fields','https://earthquake.usgs.gov/earthquakes/feed/v1.0/csv.php')]

CAPTIONS=[
 'Nested magnitude thresholds give different trend summaries. Each panel has its own y scale. The centred three-year mean is shown only when all three years exist.',
 'All seven regional panels share one y scale. Solid lines are M≥5; dashed lines are M≥6. Counts are not normalized by area or boundary length.',
 'The two periods each contain 13 full calendar years. Points show mean counts per calendar year. Exact rate ratios additionally adjust for 4,749 versus 4,748 exposure days.',
 'The denominator is the global M≥5 count for the same year. Regional shares sum to 100%; a share increase is not necessarily a count increase.',
 'Values are changes in time-exposure-adjusted recorded rates, not physical hazard estimates. Asterisks flag fewer than 30 events in either period. No inferential confidence intervals are implied.',
 'Preferred magnitude tags change markedly around 2012. The observed composition change does not identify a specific operational cause; mw* subsets are not homogenized magnitude series.',
 'Finite nonmissing values divided by the full annual M≥5 event count. Metadata absence does not mean zero error, and availability alone does not rank catalogue accuracy.',
 'The regional changes sum to the global change in calendar-year mean counts. This is an exact accounting identity, not a causal decomposition.',
 'The union of 30-day, 500-km windows starting at each catalogue M≥8 anchor is removed, including anchors. Overlaps count once. This diagnostic is not an aftershock classification or a declustered catalogue.'
]


def report_html(tables,summary,config,provenance):
    comparisons=tables['equal_period_comparison'];g=comparisons.loc[comparisons.region.eq('All')].set_index('threshold')
    slopes=tables['descriptive_slopes'].loc[lambda x:x.region.eq('All')].set_index('threshold')
    q=tables['period_reporting_comparison'];s=summary['sequence_sensitivity']
    sel=tables['selection_sensitivity'].query("region=='All' and threshold==5").set_index('selection')
    regional=comparisons.query("region!='All' and threshold==5")
    def figure(i):
        return f'<figure id="figure-{i}"><a href="figures/{FIGURES[i-1]}.png"><img loading="lazy" src="figures/{FIGURES[i-1]}.png" alt="{escape(FIGURES[i-1].replace("_"," "))}"></a><figcaption><strong>Figure {i}.</strong> {CAPTIONS[i-1]}</figcaption></figure>'
    periods=summary['periods'];early=f'{periods[0][0]}–{periods[0][1]}';late=f'{periods[1][0]}–{periods[1][1]}'
    global_table=table(['Threshold','Early N','Late N','Early mean/year','Late mean/year','Rate change %','Sen slope events/year/year'],[
        [f'M≥{t:g}',int(row.early_count),int(row.late_count),f'{row.early_annual_mean:.2f}',f'{row.late_annual_mean:.2f}',f'{row.rate_change_pct:+.2f}',f'{slopes.loc[t,"sen_slope_events_per_year"]:+.3f}'] for t,row in g.iterrows()])
    region_table=table(['Region','Early N','Late N','Early mean/year','Late mean/year','Rate change %','Share change pp'],[
        [r.region,int(r.early_count),int(r.late_count),f'{r.early_annual_mean:.2f}',f'{r.late_annual_mean:.2f}',f'{r.rate_change_pct:+.2f}',f'{r.share_change_pp:+.2f}'] for r in regional.itertuples()])
    availability=table(['Diagnostic','Early period','Late period'],[
        [label,f'{q.iloc[0][field]:.2f}%',f'{q.iloc[1][field]:.2f}%'] for field,label in [
            ('mw_prefix_pct','Preferred magnitude tag starts mw'),('depth_10km_pct','Depth exactly 10 km'),
            ('depth_33km_pct','Depth exactly 33 km'),('horizontalError_available_pct','Horizontal-error field available'),
            ('depthError_available_pct','Depth-error field available'),('magError_available_pct','Magnitude-error field available'),
            ('nst_available_pct','Station-count field available'),('automatic_pct','Automatic review status')]])
    diagnostics=table(['Aspect','Evidence','Interpretation'],[
        ['Population and extraction',f"{summary['n_events']:,} unique retained IDs; 26 annual batches; {summary['missing_calendar_months']} zero-count calendar months",'Complete requested time partitions; this does not establish detection completeness.'],
        ['Exposure',f'{early}: 4,749 days; {late}: 4,748 days','Use full-year counts and exact-day-adjusted rate comparisons.'],
        ['Magnitude measurement','Preferred magnitude-type composition changes','Stratify thresholds and retain types; no magnitude homogenization is assumed.'],
        ['Depth measurement','Concentrations at 10/33 km and error reporting differ','Treat these as reporting diagnostics; individual fixed-depth status is not supplied.'],
        ['Metadata availability','Quality fields have substantial temporal missingness differences','Never substitute zero for missing errors or interpret coverage as accuracy.'],
        ['Sequence dependence',f'{s["removed_unique_events"]:,} records in the union of {s["anchors"]} specified M≥8 windows','Naive independent-event Poisson errors and causal claims are avoided.'],
        ['Detection completeness','The extraction contains no events below M5','A uniform completeness magnitude cannot be established from this truncated sample.'],
        ['Regional definitions','Same priority-ordered boxes in all years; ±2° sensitivity saved','Boxes differ in area; Other is a heterogeneous catch-all.']])
    links=''.join(f'<li><a href="{escape(url)}">{escape(label)}</a></li>' for label,url in SOURCES)
    catalogue_table=table(['Period','Calendar years','Events','Mean events/calendar year'],[[r.period,int(r.calendar_years),int(r['count']),f'{r.annual_mean:.2f}'] for _,r in tables['multiyear_blocks'].query("region=='All' and threshold==5").iterrows()])
    body=f'''
<header><div class="eyebrow">DSC5002 · EXTENDED ANALYSIS · 3 NOVEMBER 2026</div><h1>Earthquake patterns across years and regions</h1><p>Recorded changes and the limits of temporal comparability</p><a href="dashboard.html">Open the offline comparison tool →</a></header>
<main><section class="lead"><h2>What changed</h2><p>The fixed USGS snapshot contains <strong>{summary['n_events']:,} M≥5 events</strong> across 2000–2025. Comparing {early} with {late}, the exposure-adjusted recorded rate changes by <strong>{g.loc[5,'rate_change_pct']:+.2f}% at M≥5</strong> and <strong>{g.loc[6,'rate_change_pct']:+.2f}% at M≥6</strong>. Regional changes differ. The M≥5 whole-window Sen slope is positive, while the equal-period count comparison is negative; this window dependence does not support a simple monotonic-increase description.</p>
<p>Scope and exposure can be matched, but measurement composition and metadata reporting are not constant. Uniform detection completeness and comparable physical hazard are <strong>not established</strong>. Existing baseline data and all 30 baseline deliverables remain byte-identical; this extension uses a separate version directory.</p></section>
<section lang="zh-CN" class="cn"><h2>中文结论</h2><p>后十三年的记录率低于前十三年，但不同震级门槛和地区的变化幅度不同。全期斜率与两段均值比较也给出不同方向，说明“持续上升”或“持续下降”都过于简单。2012 年附近震级类型构成发生明显变化，深度取值集中现象及误差字段缺失率也随时间变化；这些记录口径差异限制了物理解释。新增图表反映固定目录中的观测变化，不证明真实地震活动或灾害风险的因果变化。</p></section>
<nav><a href="#annual">Annual patterns</a><a href="#regions">Regions</a><a href="#comparability">Comparability</a><a href="#sensitivity">Sensitivity</a><a href="#methods">Definitions</a><a href="#sources">Sources</a></nav>
<section id="annual"><h2>Annual patterns depend on the chosen threshold and window</h2>{global_table}
<p>The M≥5 maximum is {int(slopes.loc[5,'maximum_count']):,} events in {int(slopes.loc[5,'maximum_year'])}; the minimum is {int(slopes.loc[5,'minimum_count']):,} in {int(slopes.loc[5,'minimum_year'])}. The full-window Sen slope is {slopes.loc[5,'sen_slope_events_per_year']:+.2f} events per calendar year per elapsed year. Omitting one calendar year at a time gives slopes from {slopes.loc[5,'leave_one_year_out_min']:+.2f} to {slopes.loc[5,'leave_one_year_out_max']:+.2f}; this is a sensitivity range, not a confidence interval. At M≥5.5 and M≥6 the full-window slopes are negative, and at M≥7 the median pairwise slope is zero.</p>
<p>These summaries describe different aspects of a fluctuating series. The 2010–2011 peak affects the early-half average; start/end values, robust slopes and period means need not agree. No p-value is used to convert any of them into a claim about global underlying seismicity.</p>{figure(1)}
<h3>Multi-year context</h3>{catalogue_table}<p>The last block spans six years, so compare annual means or day-adjusted rates rather than unscaled block totals. <a href="tables/descriptive_slopes.csv">Slopes and omitted-year ranges</a> · <a href="tables/multiyear_blocks.csv">all regional block statistics</a>.</p></section>
<section id="regions"><h2>Regions change differently</h2>{region_table}<p>The strongest M≥5 recorded-rate decline among the named boxes is in Indonesia and Philippines ({regional.set_index('region').loc['Indonesia and Philippines','rate_change_pct']:+.2f}%). Mediterranean and Himalaya increases by {regional.set_index('region').loc['Mediterranean and Himalaya','rate_change_pct']:+.2f}%. Other increases too, but it aggregates all locations outside the named boxes and has no single tectonic interpretation. A change in a region's global share is a composition change, not an area-normalized activity rate.</p>{figure(2)}{figure(3)}{figure(4)}{figure(8)}
<p>Results retain identical geographic definitions in both periods. The <a href="tables/region_box_period_sensitivity.csv">±2-degree box sensitivity</a> quantifies dependence on that choice without claiming invariance. Tables: <a href="tables/annual_region_threshold.csv">annual counts/shares</a> · <a href="tables/equal_period_comparison.csv">period counts/rates</a>.</p></section>
<section id="comparability"><h2>What is comparable and what remains uncertain</h2>{diagnostics}<h3>Measurement and reporting differences</h3>{availability}
<p>The share of preferred magnitude tags beginning with mw falls from {q.iloc[0].mw_prefix_pct:.2f}% to {q.iloc[1].mw_prefix_pct:.2f}%. On an annual basis it changes from 69.94% in 2011 to 37.34% in 2012. This observed mix change is not attributed to a specific policy or network change without supporting evidence. Different magnitude methods have different applicable ranges and may saturate; filtering to mw* tags changes the selection as well as the measurement mix. It is not a homogenization procedure. See <a href="{SOURCES[2][1]}">USGS magnitude-type definitions</a>.</p>
<p>Depth exactly 10 km rises from {q.iloc[0].depth_10km_pct:.2f}% to {q.iloc[1].depth_10km_pct:.2f}%, while exact 33 km becomes less common. USGS explains that fixed depth values can be assigned when depth is poorly constrained. Exact equality alone cannot identify which individual events were fixed. All such observations remain in the data. See <a href="{SOURCES[3][1]}">USGS depth-reporting explanation</a>.</p>
<p>Early error-field availability is especially low. Missing uncertainty metadata cannot be read as zero uncertainty, and improved field population alone does not prove better event measurement. The audit retains missingness separately from validity. Network codes are also tabulated by year in <a href="tables/annual_network_mix.csv">annual_network_mix.csv</a>; the contributing network is not a direct count of operational stations.</p>{figure(6)}{figure(7)}
<p>USGS notes that reporting/detection and natural clustering can change catalogue counts. This general caution does not identify the cause of this project's specific differences. The saved snapshot avoids mixing downloads across this analysis, while future catalogue revisions can still change results. No lower-magnitude sample, completeness model, uniform remeasurement or independent reference catalogue is available here, so equal detection completeness remains unresolved. <a href="tables/annual_reporting_profile.csv">Annual/regional metadata profile</a> · <a href="tables/period_reporting_comparison.csv">period diagnostics</a> · <a href="tables/monthly_coverage.csv">312-month coverage check</a>.</p></section>
<section id="sensitivity"><h2>Threshold and sequence sensitivity</h2>{figure(5)}
<p>Raising the threshold does not reverse the global equal-period decline, but it changes its size. Small regional counts are flagged because ratios can be unstable. Reviewed-only M≥5 selection gives {sel.loc['Reviewed only','rate_change_pct']:+.2f}%; mw-prefix selection gives {sel.loc['mw-prefix types','rate_change_pct']:+.2f}%, which is strongly exposed to the changing availability of those preferred types.</p>
<p>The specified-window diagnostic finds {s['anchors']} M≥8 anchors and removes {s['removed_unique_events']:,} unique events, leaving {s['kept_events']:,}. It includes anchors, respects date-line geometry, counts overlapping windows only once, and has {s['incomplete_anchor_windows']} windows extending beyond the study. The M≥5 period comparison becomes {sel.loc['Outside M8+ windows','rate_change_pct']:+.2f}%. This demonstrates sensitivity to selected clusters; it does not identify aftershocks or produce independent background events.</p>{figure(9)}
<p><a href="tables/selection_sensitivity.csv">All regional/threshold selection comparisons</a> · <a href="tables/window_removal_annual.csv">window-removal annual series</a>. The 30-day and 500-km choices are descriptive checks, not a physical rupture model or universal declustering rule.</p></section>
<section id="methods"><h2>Definitions and reproducibility</h2><p>The event unit is a unique preferred USGS earthquake ID. Dates use UTC. Annual grids include all 26 years and every configured region, with explicit zeros. Thresholds are M≥5, 5.5, 6 and 7. Magnitude values and types are not converted. Geographic boxes and priority order are identical to the baseline. Regional shares divide by the same year's global count at the same threshold.</p>
<p>Count per calendar year is the observed annual count; period annual means divide by the number of full calendar years. Exposure-standardized rates multiply counts by 365.2425/exposure-days. Rate ratios divide late by early exposure-standardized rates; zero early counts yield an undefined ratio. The Sen slope is the median of all distinct-year pairwise slopes. Omitted-year ranges are sensitivity diagnostics, not sampling intervals. Sequence windows use [anchor time, anchor time+30 days) and spherical epicentral distance ≤500 km on the same radius as the baseline.</p>
<p>Run <code>python run_temporal_analysis.py</code> after building the baseline, then <code>python verify_temporal_analysis.py</code> and <code>python -m pytest -q</code>. Use <code>--publish</code> to prepare the aggregate report, figures, tables and interactive tool under <code>docs/temporal_regional_v2</code>. Event-level inputs and window membership stay local. Baseline input/output hashes are checked before and after the extension. Dataset SHA256: <code>{provenance['dataset_sha256']}</code>. Source extraction dates: {escape(provenance['source_access_dates'])}.</p></section>
<section id="sources"><h2>Sources</h2><ol>{links}</ol><p>Official documentation was checked on 3 November 2026. It supplies interpretation limits; all reported project statistics are computed from the saved 30 October catalogue snapshot. This report makes no causal, prediction or uniform-completeness claim.</p></section></main><footer>DSC5002 · Versioned annual and regional extension · 2026-11-03</footer>'''
    css='''*{box-sizing:border-box}body{margin:0;color:#23394b;background:white;font:16px/1.65 "Segoe UI",sans-serif}header{background:#102b42;color:#fff;padding:40px max(5vw,24px)}h1{font-size:38px;line-height:1.2;max-width:1000px}header p{color:#c5dcea;font-size:21px}header a{color:#d6eafb}.eyebrow{font-size:12px;letter-spacing:1.6px;color:#9ec3df}main{max-width:1190px;margin:auto;padding:28px}.lead{font-size:18px}.cn{background:#eff4f7;padding:18px 22px;border-left:3px solid #2166ac}h2{font-size:26px;line-height:1.3;margin:36px 0 14px}h3{font-size:20px}a{color:#2166ac}nav{display:flex;gap:20px;flex-wrap:wrap;padding:25px 0;border-bottom:1px solid #dbe4eb}.table-wrap{overflow:auto;margin:22px 0}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}td,th{padding:10px 12px;text-align:left;border-bottom:1px solid #dce4ea;vertical-align:top}th{background:#eef3f7}figure{margin:32px 0 42px}img{width:100%;height:auto;border:1px solid #e4eaee}figcaption{font-size:13px;color:#526a7a;padding-top:10px}code{overflow-wrap:anywhere;background:#eff4f7;padding:2px 5px;font-size:13px}footer{text-align:center;color:#61798b;padding:25px;border-top:1px solid #dce4ea;font-size:12px}@media(max-width:650px){main{padding:18px}header{padding:26px 20px}h1{font-size:30px}h2{font-size:23px}.lead{font-size:16px}}@media print{header{background:white;color:#23394b;padding:0}header p,header a,.eyebrow{color:#23394b}main{padding:0}nav,footer{display:none}figure{break-inside:avoid}h2,h3{break-after:avoid}}'''
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Earthquake annual and regional comparisons</title><style>'+css+'</style></head><body>'+body+'</body></html>'


def build_temporal_views(tables,summary,config,provenance,root,output):
    (output/'report.html').write_text(report_html(tables,summary,config,provenance),encoding='utf-8',newline='\n')
    payload={'annual':records(tables['annual_region_threshold']),'comparisons':records(tables['equal_period_comparison']),
        'regions':['All']+[r['name'] for r in config['regions']]+['Other'],'summary':summary}
    html=(root/'web/temporal_dashboard.html').read_text(encoding='utf-8')
    html=html.replace('/*__PLOTLY__*/',get_plotlyjs()).replace('/*__DATA__*/',safe_json(payload))
    html=html.replace('/*__APP__*/',(root/'web/temporal_dashboard.js').read_text(encoding='utf-8'))
    (output/'dashboard.html').write_text(html,encoding='utf-8',newline='\n')
    return [output/'report.html',output/'dashboard.html']
