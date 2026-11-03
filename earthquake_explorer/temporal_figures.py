"""Additional scientific figures; the twelve baseline figures stay untouched."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from .figures import BLUE,GOLD,PURPLE,REGION_COLORS
from .temporal_analysis import QUALITY_FIELDS

FIGURES=[
 '01_annual_threshold_trends','02_regional_annual_trends','03_equal_period_regions',
 '04_regional_share_heatmap','05_threshold_sensitivity','06_magnitude_type_mix',
 '07_reporting_availability','08_regional_change_contributions','09_window_sensitivity']


def make_temporal_figures(tables,summary,config,output):
    output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'figure.facecolor':'white','savefig.facecolor':'white'})
    panel=tables['annual_region_threshold'];comp=tables['equal_period_comparison']
    regions=[r['name'] for r in config['regions']]+['Other'];years=np.arange(config['start_year'],config['end_year']+1)
    periods=summary['periods'];early=f'{periods[0][0]}–{periods[0][1]}';late=f'{periods[1][0]}–{periods[1][1]}'
    def save(fig,index,note):
        fig.text(.02,.018,f"USGS snapshot 2026-10-30 | {config['start_year']}–{config['end_year']} UTC | {summary['n_events']:,} M≥5 events\n"+note,
            fontsize=8,color='#526373',va='bottom')
        fig.tight_layout(rect=(0,.10,1,.94));fig.savefig(output/(FIGURES[index-1]+'.png'),dpi=175);plt.close(fig)
    def calendar_axis(ax):
        ax.set_xticks([2000,2005,2010,2015,2020,2025]);ax.set_xlim(years[0]-.4,years[-1]+.4)

    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,threshold in zip(axes.flat,[5,5.5,6,7]):
        p=panel.loc[panel.region.eq('All')&panel.threshold.eq(threshold)]
        ax.plot(p.year,p['count'],color=BLUE,marker='o',ms=3,lw=1.4,label='Annual count')
        ax.plot(p.year,p.centered_3year_mean,color=GOLD,lw=2,label='Centred 3-year mean')
        ax.set(title=f'M ≥ {threshold:g} · n={p["count"].sum():,}',ylabel='Recorded events per calendar year',ylim=(0,p['count'].max()*1.13))
        calendar_axis(ax)
    axes[0,0].legend(fontsize=9);fig.suptitle('Annual patterns across magnitude thresholds',fontsize=16)
    save(fig,1,'Panels use different y ranges; the magnitude thresholds define nested populations. Smoothing omits incomplete endpoint windows.')

    fig,axes=plt.subplots(4,2,figsize=(13,11),sharex=True,sharey=True)
    ceiling=panel.loc[panel.region.ne('All')&panel.threshold.eq(5),'count'].max()*1.12
    for ax,region,color in zip(axes.flat,regions,REGION_COLORS):
        for threshold,style,label in [(5,'-','M≥5'),(6,'--','M≥6')]:
            p=panel.loc[panel.region.eq(region)&panel.threshold.eq(threshold)]
            ax.plot(p.year,p['count'],ls=style,color=color if threshold==5 else '#354b5d',lw=1.5,label=label)
        ax.set(title=region,ylim=(0,ceiling),ylabel='Recorded events');calendar_axis(ax)
    axes[0,0].legend(fontsize=9);axes.flat[-1].axis('off')
    fig.suptitle('Regional annual counts with a shared vertical scale',fontsize=16)
    save(fig,2,'Priority-ordered geographic boxes, not equal-area tectonic units. Other is a heterogeneous catch-all region.')

    fig,axes=plt.subplots(1,2,figsize=(13,6.2))
    for ax,threshold in zip(axes,[5,6]):
        p=comp.loc[comp.region.ne('All')&comp.threshold.eq(threshold)].set_index('region').reindex(regions)
        pos=np.arange(len(regions))
        ax.hlines(pos,np.minimum(p.early_annual_mean,p.late_annual_mean),np.maximum(p.early_annual_mean,p.late_annual_mean),color='#a6b3bd',lw=2)
        ax.scatter(p.early_annual_mean,pos,color=BLUE,s=38,label=early,zorder=3)
        ax.scatter(p.late_annual_mean,pos,color=GOLD,s=38,marker='D',label=late,zorder=3)
        ax.set_yticks(pos,regions if threshold==5 else ['']*len(regions));ax.invert_yaxis()
        ax.set(title=f'M ≥ {threshold:g}',xlabel='Mean recorded events per calendar year',xlim=(0,max(p.early_annual_mean.max(),p.late_annual_mean.max())*1.12))
        ax.legend(fontsize=9)
    fig.suptitle('Regional counts across two equal 13-year periods',fontsize=16)
    save(fig,3,'Annual means divide each period by 13. CSV rate ratios additionally account for the one-day leap-year exposure difference.')

    p=panel.loc[panel.threshold.eq(5)&panel.region.ne('All')].pivot(index='region',columns='year',values='global_share_pct').reindex(regions)
    fig,ax=plt.subplots(figsize=(13,5.8));im=ax.imshow(p,cmap='Blues',vmin=0,aspect='auto')
    ax.set_yticks(range(len(regions)),regions);ax.set_xticks([0,5,10,15,20,25],years[[0,5,10,15,20,25]]);ax.grid(False)
    ax.set(title='Regional share of the annual global M≥5 catalogue',xlabel='Year (UTC)');fig.colorbar(im,ax=ax,label='Share of yearly global count (%)',pad=.02)
    save(fig,4,'Every year sums to 100% across regions. A rising share does not by itself imply a rising regional count.')

    p=comp.loc[comp.region.ne('All')].pivot(index='region',columns='threshold',values='rate_change_pct').reindex(regions)
    bound=max(1,np.nanmax(np.abs(p.to_numpy())))
    fig,ax=plt.subplots(figsize=(10,6.1));im=ax.imshow(p,cmap='PuOr_r',norm=TwoSlopeNorm(vcenter=0,vmin=-bound,vmax=bound),aspect='auto')
    ax.set_xticks(range(4),['M≥5','M≥5.5','M≥6','M≥7']);ax.set_yticks(range(len(regions)),regions);ax.grid(False)
    for i in range(len(regions)):
        for j,threshold in enumerate(p.columns):
            v=p.iloc[i,j];small=comp.loc[comp.region.eq(regions[i])&comp.threshold.eq(threshold),'small_period_count'].iloc[0]
            label='undefined' if not np.isfinite(v) else f'{v:+.1f}%'+('*' if small else '')
            ax.text(j,i,label,ha='center',va='center',fontsize=10,color='white' if np.isfinite(v) and abs(v)>bound*.62 else '#1c2e3d')
    ax.set_title(f'Exposure-adjusted count-rate change · {late} versus {early}')
    fig.colorbar(im,ax=ax,label='Change in recorded count rate (%)',pad=.03)
    save(fig,5,'* Fewer than 30 events in at least one period. Zero early counts produce undefined ratios. No confidence intervals or significance tests.')

    mix=tables['annual_magnitude_type_mix'].copy()
    mix['group']=mix.magType.where(mix.magType.isin(['mb','mwc','mww','mwb']),'Other types')
    p=mix.groupby(['year','group'])['count'].sum().unstack(fill_value=0).reindex(years)
    names=['mb','mwc','mww','mwb','Other types'];p=p.reindex(columns=names,fill_value=0);shares=p.div(p.sum(axis=1),axis=0)*100
    fig,ax=plt.subplots(figsize=(12,5.6));bottom=np.zeros(len(years))
    for name,color in zip(names,[BLUE,GOLD,PURPLE,'#57823b','#82909b']):
        ax.bar(years,shares[name],bottom=bottom,color=color,width=.88,label=name);bottom+=shares[name].to_numpy()
    ax.set(title='Preferred magnitude-type composition changes over time',ylabel='Share of annual M≥5 catalogue (%)',ylim=(0,100),xlabel='Year (UTC)');calendar_axis(ax);ax.legend(ncol=5,loc='upper left',fontsize=9)
    save(fig,6,'Magnitude labels are retained as supplied; mw* tags do not form a homogenized magnitude series. The 2012 mix shift is observed, not causally attributed.')

    q=tables['annual_reporting_profile'].loc[lambda x:x.region.eq('All')].set_index('year')
    values=q[[c+'_available_pct' for c in QUALITY_FIELDS]].T
    fig,ax=plt.subplots(figsize=(12.5,5.8));im=ax.imshow(values,cmap='Blues',vmin=0,vmax=100,aspect='auto')
    ax.set_yticks(range(len(QUALITY_FIELDS)),QUALITY_FIELDS);ax.set_xticks([0,5,10,15,20,25],years[[0,5,10,15,20,25]]);ax.grid(False)
    ax.set(title='Availability of source quality fields by year',xlabel='Year (UTC)');fig.colorbar(im,ax=ax,label='Nonmissing finite values (%)',pad=.02)
    save(fig,7,'Denominator: all M≥5 events in each year. Missing metadata is not zero error; availability changes do not establish improving or worsening accuracy.')

    p=comp.loc[comp.region.ne('All')&comp.threshold.eq(5)].sort_values('annual_count_difference')
    fig,ax=plt.subplots(figsize=(11.5,5.8));pos=np.arange(len(p))
    ax.barh(pos,p.annual_count_difference,color=[BLUE if v<0 else GOLD for v in p.annual_count_difference])
    ax.set_yticks(pos,p.region);ax.axvline(0,color='#455869',lw=1);ax.invert_yaxis()
    for i,value in enumerate(p.annual_count_difference):ax.text(value+(-2 if value<0 else 2),i,f'{value:+.1f}',ha='right' if value<0 else 'left',va='center',fontsize=9)
    limit=max(abs(p.annual_count_difference.min()),abs(p.annual_count_difference.max()))*1.27;ax.set_xlim(-limit,limit)
    ax.set(title='Additive regional contributions to the M≥5 period-count difference',xlabel='Change in mean recorded events per calendar year')
    save(fig,8,f'Regional differences sum exactly to the global change of {p.annual_count_difference.sum():+.2f} events/year. This is accounting, not causal attribution.')

    fig,axes=plt.subplots(1,2,figsize=(13,5.6))
    for ax,threshold in zip(axes,[5,6]):
        full=panel.loc[panel.region.eq('All')&panel.threshold.eq(threshold)]
        reduced=tables['window_removal_annual'].loc[lambda x:x.region.eq('All')&x.threshold.eq(threshold)]
        ax.plot(full.year,full['count'],color=BLUE,label='Full preferred catalogue',marker='o',ms=3)
        ax.plot(reduced.year,reduced['count'],color=GOLD,label='Outside M8+ windows',ls='--',marker='s',ms=3)
        ax.set(title=f'M ≥ {threshold:g}',ylabel='Recorded events per calendar year',ylim=(0,full['count'].max()*1.1));calendar_axis(ax)
    axes[0].legend(fontsize=8);fig.suptitle('Sensitivity to specified large-event time and distance windows',fontsize=15)
    save(fig,9,f"Union of {summary['sequence_sensitivity']['anchors']} M≥8 anchor windows: [0,30) days and ≤500 km, anchors included; {summary['sequence_sensitivity']['removed_unique_events']:,} unique records removed. This is not declustering.")
    return [output/(name+'.png') for name in FIGURES]
