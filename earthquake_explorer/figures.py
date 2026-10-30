"""Twelve inspectable, offline research figures from the full cleaned catalogue."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .geometry import geometry_lines
from .analysis import DEPTH_ORDER, select_anchor, case_sample, magnitude_frequency

BLUE = '#2166ac'
GOLD = '#cc8b19'
PURPLE = '#8e4b98'
DEPTH_COLORS = {'Shallow':BLUE,'Intermediate':GOLD,'Deep':PURPLE,'Missing':'#777777'}
REGION_COLORS = ['#2166ac','#b06816','#8e4b98','#57823b','#b14f76','#4b8793','#656565']
FIGURE_NAMES = [
    '01_annual_counts','02_region_year_heatmap','03_global_depth_map',
    '04_boundary_distance_histogram','05_regional_boundary_ecdf','06_depth_distribution',
    '07_regional_depth_boxplots','08_regional_cross_sections','09_magnitude_distribution',
    '10_magnitude_frequency','11_pairwise_relationships','12_major_event_windows']


def draw_depth_histogram(ax,frame,edges):
    names=DEPTH_ORDER[:3]
    values=[frame.loc[frame.depth_class.eq(name),'depth'] for name in names]
    ax.hist(values,bins=edges,stacked=True,color=[DEPTH_COLORS[name] for name in names],
            label=[f'{name} (n={len(v):,})' for name,v in zip(names,values)],edgecolor='white',lw=.2)


def split_dateline(line):
    for part in np.split(line,np.where(np.abs(np.diff(line[:,0]))>180)[0]+1):
        if len(part)>1:
            yield part


def draw_lines(ax, layer, color='#a6afb6', width=.5, alpha=1):
    for line in geometry_lines(layer):
        for part in split_dateline(line):
            ax.plot(part[:,0],part[:,1],color=color,lw=width,alpha=alpha,zorder=1)


def world_axes(ax, coast, boundaries=None):
    ax.set_facecolor('#f5f8fb')
    draw_lines(ax,coast,'#8795a2',.5)
    if boundaries:
        draw_lines(ax,boundaries,'#555555',.55,.8)
    ax.set(xlim=(-180,180),ylim=(-90,90),xlabel='Longitude (degrees)',ylabel='Latitude (degrees)')
    ax.set_aspect('equal',adjustable='box')


def make_figures(frame,config,root):
    output = root/'outputs/figures'
    output.mkdir(parents=True,exist_ok=True)
    coast = json.loads((root/'data/raw/geography/ne_110m_coastline.geojson').read_text(encoding='utf-8'))
    boundaries = json.loads((root/'data/raw/geography/PB2002_boundaries.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                         'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
                         'grid.alpha':.17,'figure.facecolor':'white','savefig.facecolor':'white'})
    scope = f"USGS | {config['start_year']}–{config['end_year']} UTC | M ≥ {config['min_magnitude']:g} | n = {len(frame):,}"
    def save(fig,index,note=''):
        fig.text(.02,.016,scope+('\n'+note if note else ''),fontsize=8,color='#505966',ha='left',va='bottom')
        fig.tight_layout(rect=(0,.075,1,.96))
        fig.savefig(output/(FIGURE_NAMES[index-1]+'.png'),dpi=170)
        plt.close(fig)

    years=np.arange(config['start_year'],config['end_year']+1)
    annual=frame.groupby('year').size().reindex(years,fill_value=0)
    fig,ax=plt.subplots(figsize=(11,5))
    ax.plot(years,annual,color=BLUE,marker='o',ms=4,lw=1.8)
    ax.set(title='RQ1  Recorded earthquakes by year',xlabel='Year (UTC)',ylabel='Earthquake count',ylim=(0,annual.max()*1.15))
    ax.set_xticks([years[0],2005,2010,2015,2020,years[-1]])
    save(fig,1,'Catalogue counts reflect monitoring and sequence clustering; they are not hazard forecasts.')

    regions=[r['name'] for r in config['regions']]+['Other']
    heat=pd.crosstab(frame.region,frame.year).reindex(index=regions,columns=years,fill_value=0)
    fig,ax=plt.subplots(figsize=(12,5.4))
    im=ax.imshow(heat,cmap='Blues',aspect='auto',vmin=0)
    ax.set_yticks(range(len(regions)),regions)
    ax.set_xticks(range(0,len(years),3),years[::3])
    ax.set(title='RQ1  Regional catalogue counts by year',xlabel='Year (UTC)')
    ax.grid(False)
    fig.colorbar(im,ax=ax,label='Earthquake count',pad=.02)
    save(fig,2,'Geographic boxes are defined in config.json; counts are not normalized by area.')

    fig,ax=plt.subplots(figsize=(13,6.7))
    world_axes(ax,coast,boundaries)
    for name in DEPTH_ORDER:
        part=frame.loc[frame.depth_class.eq(name)]
        if len(part):
            ax.scatter(part.longitude,part.latitude,s=3.5,c=DEPTH_COLORS[name],alpha=.55,label=f'{name} (n={len(part):,})',zorder=2,linewidths=0,rasterized=True)
    ax.legend(loc='lower left',fontsize=8,framealpha=.95)
    ax.set_title('RQ1 / RQ3  Global epicentres, depth classes and PB2002 boundaries')
    save(fig,3,'Shallow <70 km; intermediate 70–<300 km; deep ≥300 km. Equal-size markers; events overlap.')

    fig,ax=plt.subplots(figsize=(10,5.2))
    distance=frame.boundary_distance_km
    bins=np.r_[0,np.geomspace(.1,max(1,distance.max()),65)]
    ax.hist(distance,bins=bins,color=BLUE,edgecolor='white',lw=.2)
    ax.set_xscale('symlog',linthresh=1)
    ax.set(title='RQ2  Distance to the nearest mapped boundary',xlabel='Spherical segment distance (km; logarithmic above 1 km)',ylabel='Earthquake count')
    save(fig,4,'Exact minor great-circle arcs on a sphere (R=6371.0088 km); PB2002 map and geometry remain approximations.')

    fig,ax=plt.subplots(figsize=(11,5.5))
    for region,color in zip(regions,REGION_COLORS):
        values=np.sort(frame.loc[frame.region.eq(region),'boundary_distance_km'].to_numpy())
        if len(values):
            ax.step(values,np.arange(1,len(values)+1)/len(values)*100,where='post',label=f'{region} (n={len(values):,})',color=color,lw=1.5)
    ax.set_xscale('symlog',linthresh=1)
    ax.set(title='RQ2  Regional cumulative boundary distances',xlabel='Nearest mapped boundary (km; logarithmic above 1 km)',ylabel='Events at or below distance (%)',ylim=(0,101))
    ax.legend(fontsize=8,loc='lower right')
    save(fig,5,'Each curve uses its own regional denominator; boxes are descriptive, not tectonic classifications.')

    fig,ax=plt.subplots(figsize=(10,5.3))
    depth=frame.depth.dropna()
    edges=np.linspace(min(-10,depth.min()),max(710,depth.max()+1),74)
    draw_depth_histogram(ax,frame,edges)
    ax.axvline(70,color='#555',ls='--',lw=1)
    ax.axvline(300,color='#555',ls=':',lw=1)
    ax.set(title='RQ3  Recorded hypocentre depths',xlabel='Depth (km)',ylabel='Earthquake count')
    ax.legend(fontsize=9)
    save(fig,6,f'Missing depth: {frame.depth.isna().sum():,}; negative catalogue depths retained: {frame.depth.lt(0).sum():,}.')

    fig,ax=plt.subplots(figsize=(11,6))
    values=[frame.loc[frame.region.eq(r),'depth'].dropna().to_numpy() for r in regions]
    bp=ax.boxplot(values,vert=False,patch_artist=True,showfliers=True,
                  flierprops={'markersize':1.5,'alpha':.15},medianprops={'color':'#202730','lw':1.5})
    for box,color in zip(bp['boxes'],REGION_COLORS):box.set_facecolor(color);box.set_alpha(.6)
    ax.set_yticks(np.arange(1,len(regions)+1),[f'{r} (n={len(v):,})' for r,v in zip(regions,values)])
    ax.set(title='RQ3  Regional depth distributions',xlabel='Depth (km)')
    ax.invert_yaxis()
    save(fig,7,'Boxes show the median and IQR; whiskers extend to 1.5 IQR; small points are outlying recorded depths.')

    fig,axes=plt.subplots(1,2,figsize=(12,5.3),sharey=True)
    for ax,region in zip(axes,['Japan and Kuril','Tonga Kermadec Fiji']):
        part=frame.loc[frame.region.eq(region)&frame.depth.notna()]
        x=part.longitude.to_numpy().copy()
        if region.startswith('Tonga'):x=np.where(x<0,x+360,x)
        ax.scatter(x,part.depth,s=5,c=[DEPTH_COLORS[v] for v in part.depth_class],alpha=.45,linewidths=0)
        ax.set(title=f'{region} (n={len(part):,})',xlabel='Longitude (degrees east, unwrapped)')
        ax.axhline(70,color='#666',ls='--',lw=.7);ax.axhline(300,color='#666',ls=':',lw=.7)
    axes[0].set_ylabel('Depth (km; positive down)')
    axes[0].invert_yaxis()
    fig.suptitle('RQ3  Longitude–depth projections through the regional boxes',fontsize=14)
    save(fig,8,'All latitudes in each box are projected together; these are not narrow trench-normal sections. Vertical scale is exaggerated.')

    fig,ax=plt.subplots(figsize=(10,5.2))
    ax.hist(frame.mag,bins=np.arange(5,10.01,.1),color=BLUE,edgecolor='white',lw=.3)
    ax.set(title='RQ4  Recorded magnitude distribution',xlabel='Preferred catalogue magnitude (mixed magnitude types)',ylabel='Earthquake count',xlim=(5,9.5))
    save(fig,9,'Extraction is censored below M5; preferred catalogue magnitudes are not converted to a homogeneous moment-magnitude scale.')

    freq=magnitude_frequency(frame.mag)
    fig,ax=plt.subplots(figsize=(10,5.2))
    ax.step(freq.magnitude,freq.cumulative_count,where='pre',color=BLUE,lw=1.8)
    ax.set_yscale('log')
    ax.set(title='RQ4  Cumulative magnitude frequency',xlabel='Magnitude threshold m',ylabel='Recorded events with M ≥ m (log scale)',xlim=(5,9.5))
    save(fig,10,'Descriptive survival counts for the fixed 26-year window. No fitted forecast or completeness-adjusted b-value.')

    fig,axes=plt.subplots(1,3,figsize=(15,5.1))
    for ax,(x,y,xlabel,ylabel) in zip(axes,[('mag','depth','Magnitude','Depth (km)'),
        ('mag','boundary_distance_km','Magnitude','Boundary distance (km)'),('boundary_distance_km','depth','Boundary distance (km)','Depth (km)')]):
        part=frame[[x,y]].dropna()
        im=ax.hexbin(part[x],part[y],gridsize=38,mincnt=1,cmap='Blues',bins='log',linewidths=0)
        ax.set(xlabel=xlabel,ylabel=ylabel)
        fig.colorbar(im,ax=ax,label='Count (log color)',pad=.02,shrink=.85)
    fig.suptitle('Exploratory pairwise relationships',fontsize=14)
    save(fig,11,'All available pairs; Spearman coefficients and subgroup checks are saved in outputs/tables. Associations do not establish causation.')

    fig,axes=plt.subplots(len(config['cases']),2,figsize=(13,12),squeeze=False)
    for row,case in enumerate(config['cases']):
        anchor=select_anchor(frame,case)
        sample,stats=case_sample(frame,anchor,config['case_window_days'],config['case_radius_km'],config['start_year'],config['end_year'])
        ax,timeline=axes[row]
        offset=lambda x: anchor.longitude+(np.asarray(x)-anchor.longitude+180)%360-180
        for line in geometry_lines(coast):
            xx=offset(line[:,0])
            for part in split_dateline(np.column_stack([xx,line[:,1]])):
                ax.plot(part[:,0],part[:,1],color='#adb7bf',lw=.6,zorder=0)
        for before,color,label in [(True,BLUE,'Before'),(False,GOLD,'After')]:
            group=sample.loc[sample.relative_days.lt(0) if before else sample.relative_days.ge(0)]
            ax.scatter(offset(group.longitude),group.latitude,s=10,c=color,label=f'{label} (n={len(group)})',alpha=.6,linewidths=0)
        ax.scatter([anchor.longitude],[anchor.latitude],s=110,marker='*',c='#202730',label=f'Anchor M{anchor.mag:g}',zorder=5)
        lat_span=config['case_radius_km']/111.195*1.15
        lon_span=lat_span/max(.2,np.cos(np.deg2rad(anchor.latitude)))
        ax.set(xlim=(anchor.longitude-lon_span,anchor.longitude+lon_span),ylim=(anchor.latitude-lat_span,anchor.latitude+lat_span),
            xlabel='Longitude (degrees, centred on anchor)',ylabel='Latitude (degrees)',title=case['name'])
        ax.legend(fontsize=7,loc='lower left')
        edges=np.arange(-config['case_window_days'],config['case_window_days']+1)
        counts,_=np.histogram(sample.relative_days,bins=edges)
        timeline.bar(edges[:-1]+.5,counts,width=.95,color=[BLUE if e<0 else GOLD for e in edges[:-1]])
        timeline.axvline(0,color='#202730',lw=1.1,ls='--')
        timeline.set(xlabel='Days relative to anchor (UTC; one-day bins)',ylabel='M ≥ 5 events per bin',
            title=f'±{config["case_window_days"]} days, {config["case_radius_km"]} km; anchor excluded',xlim=(-30,30))
    fig.suptitle('RQ5  Recorded sequences around selected major earthquakes',fontsize=14)
    save(fig,12,'Fixed windows [−30,0) and [0,30) days; anchor excluded. M≥5 events only; no causal aftershock attribution.')
    return [output/(name+'.png') for name in FIGURE_NAMES]
