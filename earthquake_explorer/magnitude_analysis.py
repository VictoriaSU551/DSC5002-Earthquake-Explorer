"""Reproduce Member 4 / RQ4 tables and figures from the included USGS snapshot."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

ROOT = Path(__file__).resolve().parents[1]
MW_TYPES = {'mw', 'mwb', 'mwc', 'mwr', 'mww', 'mwp'}
BINS = np.arange(50, 101) / 10  # fixed 0.1 bins; avoids floating boundary errors
THRESHOLDS = np.arange(50, 96) / 10
COLORS = ['#2166ac', '#b47819', '#8e4b98', '#46816c']


def export(frame, path):
    frame.to_csv(path, index=False, encoding='utf-8-sig', float_format='%.10g')


def load_data(data_dir):
    # Adopted from Member 4; every final analysis now uses the same sealed input.
    from earthquake_explorer.temporal_inputs import load_verified_snapshot
    d=load_verified_snapshot(ROOT)
    d['mag_type_original']=d.magType
    d['magType']=d.magType.fillna('unknown').str.strip().str.lower()
    d['magnitude_family']=np.where(d.magType.isin(MW_TYPES),'Mw family',np.where(d.magType.eq('mb'),'mb','Other'))
    d['period']=np.where(d.year.le(2012),'2000–2012','2013–2025')
    d['relative_energy_proxy_m5']=10.0**(1.5*(d.mag-5))
    audit=pd.DataFrame([{'step':'Loaded verified earthquake-only snapshot','rows_before':len(d),'rows_removed':0,'rows_retained':len(d)}])
    raw_types=pd.DataFrame([{'event_type':'earthquake','n':len(d)}])
    return d,audit,raw_types,[ROOT/'data/processed/earthquakes.csv']


def cumulative(values, thresholds):
    # searchsorted gives inclusive N(M>=m), including threshold ties.
    values = np.sort(np.asarray(values, dtype=float))
    return len(values) - np.searchsorted(values, thresholds, side='left')


def save_figure(fig, out, name, note):
    fig.text(.08, .025, note, ha='left', va='bottom', fontsize=9, color='#536778')
    fig.savefig(out / f'{name}.png', dpi=220, facecolor='white')
    fig.savefig(out / f'{name}.svg', facecolor='white')
    plt.close(fig)


def run(data_dir, output_dir):
    figures = output_dir / 'figures'; tables = output_dir / 'tables'
    figures.mkdir(parents=True, exist_ok=True); tables.mkdir(parents=True, exist_ok=True)
    d, audit, raw_types, source_paths = load_data(data_dir)
    export(audit, tables / 'cleaning_audit.csv'); export(raw_types, tables / 'source_event_types.csv')
    export(d, output_dir / 'data' / 'member4_analysis_dataset.csv')
    summary = d.mag.describe(percentiles=[.25,.5,.75,.9,.95,.99]).rename_axis('statistic').reset_index(name='value')
    export(summary, tables / 'magnitude_summary.csv')
    counts, _ = np.histogram(d.mag, BINS)
    hist = pd.DataFrame({'lower_inclusive': BINS[:-1], 'upper_exclusive': BINS[1:], 'n': counts})
    hist['percent'] = hist.n / len(d) * 100
    export(hist, tables / 'magnitude_histogram.csv')
    band_index = pd.cut(d.mag, [5,6,7,8,10], right=False, labels=['5.0–<6.0','6.0–<7.0','7.0–<8.0','8.0–<10.0'])
    if band_index.isna().any(): raise ValueError('Magnitude outside fixed plotting range [5,10).')
    band = d.groupby(band_index, observed=False).agg(n=('id','size'), relative_proxy_sum=('relative_energy_proxy_m5','sum')).reset_index(names='magnitude_band')
    band['count_percent'] = band.n / len(d) * 100
    band['proxy_percent'] = band.relative_proxy_sum / band.relative_proxy_sum.sum() * 100
    export(band, tables / 'magnitude_band_summary.csv')
    groups = {'All types':d, 'Mw family':d[d.magType.isin(MW_TYPES)], 'mb':d[d.magType.eq('mb')]}
    curves = []
    for name, sub in groups.items():
        for period in ['All years', '2000–2012', '2013–2025']:
            s = sub if period == 'All years' else sub[sub.period.eq(period)]
            if not len(s): continue
            n = cumulative(s.mag, THRESHOLDS)
            curves.append(pd.DataFrame({'sample':name,'period':period,'threshold':THRESHOLDS,'n_ge':n,'sample_n':len(s),'percent_ge':n/len(s)*100,'annual_mean_ge':n/(26 if period=='All years' else 13)}))
    curves = pd.concat(curves, ignore_index=True); export(curves, tables / 'cumulative_frequency.csv')
    type_summary = d.groupby(['magType','magnitude_family']).agg(n=('id','size'),minimum=('mag','min'),median=('mag','median'),maximum=('mag','max')).reset_index().sort_values('n',ascending=False)
    type_summary['percent'] = type_summary.n / len(d)*100
    export(type_summary, tables / 'magnitude_type_summary.csv')
    composition = pd.crosstab(d.year, d.magnitude_family).reindex(range(2000,2026),fill_value=0)
    export(composition.reset_index(), tables / 'annual_magnitude_types.csv')
    relative = pd.DataFrame({'magnitude':np.arange(5,10), 'relative_energy_proxy_m5':10.0**(1.5*(np.arange(5,10)-5))})
    export(relative, tables / 'relative_energy_scale.csv')
    export(d.sort_values(['mag','time'],ascending=[False,True]).head(20)[['id','time','mag','magType','place','region']],tables / 'largest_events.csv')

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.titlepad':14,'svg.fonttype':'none'})
    fig, ax = plt.subplots(figsize=(11,6.5));fig.subplots_adjust(left=.09,right=.97,bottom=.18,top=.85)
    ax.bar(BINS[:-1], counts, width=.095, align='edge', color=COLORS[0])
    ax.set(xlabel='Catalogue magnitude M (0.1-unit bins)',ylabel='Recorded earthquake count',xlim=(4.95,9.55))
    fig.suptitle('RQ4 · Magnitude distribution', x=.09, y=.96, ha='left', fontsize=19, fontweight='bold')
    fig.subplots_adjust(top=.81)
    ax.text(0,1.04,f'Global | 2000–2025 | M ≥ 5.0 | n = {len(d):,}',transform=ax.transAxes,color='#536778')
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'));ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
    ax.text(.97,.92,f'Median: {d.mag.median():.1f}\nM < 6: {100*d.mag.lt(6).mean():.1f}%\nM ≥ 8: {d.mag.ge(8).sum():,}',transform=ax.transAxes,ha='right',va='top',linespacing=1.7)
    save_figure(fig,figures,'rq4_01_magnitude_distribution','Source: included USGS snapshot. Mixed catalogue magnitude types; extremes are retained.')

    fig, ax = plt.subplots(figsize=(11,6.5));fig.subplots_adjust(left=.09,right=.97,bottom=.18,top=.85)
    c=curves[(curves['sample']=='All types') & (curves.period=='All years')];c=c[c.n_ge.gt(0)]
    ax.step(c.threshold,c.n_ge,where='pre',color=COLORS[0],lw=2);ax.scatter(c.threshold,c.n_ge,s=12,color=COLORS[0])
    for m in [5,6,7,8,9]:
        n=int(cumulative(d.mag,[m])[0]);ax.annotate(f'M ≥ {m}: {n:,}',(m,n),xytext=(7,8),textcoords='offset points',fontsize=10)
    ax.set(yscale='log',xlabel='Magnitude threshold m',ylabel='Cumulative count N(M ≥ m)',xlim=(4.95,9.55),ylim=(.8,len(d)*2.3))
    ax.set_title('RQ4 · Cumulative magnitude–frequency pattern',loc='left',fontsize=19)
    ax.grid(alpha=.18,which='both');save_figure(fig,figures,'rq4_02_cumulative_frequency','Inclusive threshold counts; logarithmic count axis. Descriptive catalogue pattern, without a fitted prediction model.')

    fig, axes = plt.subplots(1,2,figsize=(13,6.5));fig.subplots_adjust(left=.07,right=.97,bottom=.2,top=.78,wspace=.28)
    fig.suptitle('RQ4 · Magnitude-type sensitivity',x=.07,ha='left',fontsize=19,fontweight='bold',y=.95)
    for j,(name,sub) in enumerate(groups.items()):
        c=curves[(curves['sample']==name)&(curves.period=='All years')&curves.n_ge.gt(0)]
        axes[0].step(c.threshold,c.percent_ge,where='pre',lw=2,color=COLORS[j],label=f'{name} (n={len(sub):,})')
    axes[0].set(yscale='log',xlabel='Magnitude threshold m',ylabel='Within-sample events ≥ m (%)',title='A · Normalized cumulative distributions',xlim=(5,9.5))
    axes[0].legend(fontsize=9,frameon=False);axes[0].grid(alpha=.15,which='both')
    shares=composition.div(composition.sum(axis=1),axis=0)*100
    bottom=np.zeros(len(shares))
    for j,name in enumerate(['Mw family','mb','Other']):
        vals=shares.get(name,pd.Series(0,index=shares.index)).values
        axes[1].bar(shares.index,vals,bottom=bottom,color=COLORS[j+1 if j<2 else 0],label=name,width=.85);bottom+=vals
    axes[1].set(xlabel='UTC year',ylabel='Share of annual recorded events (%)',ylim=(0,100),title='B · Catalogue type composition over time')
    axes[1].set_xticks([2000,2005,2010,2015,2020,2025]);axes[1].legend(fontsize=9,frameon=False,loc='lower right')
    save_figure(fig,figures,'rq4_03_magnitude_type_sensitivity','Mw family = mw, mwb, mwc, mwr, mww, mwp. Subsets overlap “All types”; type selection is not random.\nDifferent type mixtures can affect pooled comparisons. These plots do not establish equal completeness or scale equivalence.')

    fig, axes=plt.subplots(1,2,figsize=(13,6.5));fig.subplots_adjust(left=.07,right=.97,bottom=.22,top=.8,wspace=.30)
    fig.suptitle('RQ4 · Relative energy scale (illustrative proxy)',x=.07,y=.95,ha='left',fontsize=19,fontweight='bold')
    axes[0].plot(relative.magnitude,relative.relative_energy_proxy_m5,marker='o',color=COLORS[1],lw=2)
    axes[0].set(yscale='log',xlabel='Magnitude M',ylabel='Relative proxy (M5 = 1)',title=r'A · $R(M)=10^{1.5(M-5)}$',xticks=range(5,10),ylim=(.3,8e6))
    for m,r in relative.itertuples(index=False,name=None):axes[0].annotate(f'{r:,.1f}×' if r<100 else f'{r:,.0f}×',(m,r),xytext=(0,12),textcoords='offset points',ha='center',fontsize=9)
    axes[0].grid(alpha=.15,which='both')
    x=np.arange(len(band));axes[1].bar(x-.18,band.count_percent,width=.36,color=COLORS[0],label='Event count share');axes[1].bar(x+.18,band.proxy_percent,width=.36,color=COLORS[1],label='Summed proxy share')
    axes[1].set(xticks=x,xticklabels=band.magnitude_band,xlabel='Magnitude band',ylabel='Share within full catalogue (%)',ylim=(0,105),title='B · Event counts and summed proxy')
    axes[1].legend(frameon=False,fontsize=9)
    for k,row in enumerate(band.itertuples()):
        for dx,val in [(-.18,row.count_percent),(.18,row.proxy_percent)]:axes[1].text(k+dx,val+1.2,f'{val:.1f}',ha='center',fontsize=9)
    save_figure(fig,figures,'rq4_04_relative_energy_scale','Conventional 1.5-exponent scaling; mixed magnitude types. Dimensionless illustration, not measured energy in joules.\nSummed proxy shares depend strongly on extreme events and the selected catalogue; they do not measure damage or risk.')
    checks={'event_count':len(d),'unique_ids':bool(d.id.is_unique),'matches_group_ids_and_magnitudes':True,'histogram_total':int(counts.sum()),'band_total':int(band.n.sum()),'cumulative_at_5':int(cumulative(d.mag,[5])[0]),'cumulative_nonincreasing':bool(np.all(np.diff(cumulative(d.mag,THRESHOLDS))<=0)),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__}}
    assert checks['histogram_total']==checks['band_total']==checks['cumulative_at_5']==len(d)
    (tables/'validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(f'Completed RQ4: {len(d):,} earthquakes; 4 PNG + 4 SVG figures; {len(list(tables.glob("*.csv")))} CSV tables.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'outputs/final/rq4')
    args=parser.parse_args()
    (args.output_dir/'data').mkdir(parents=True,exist_ok=True)
    run(args.data_dir,args.output_dir)

if __name__=='__main__':
    main()
