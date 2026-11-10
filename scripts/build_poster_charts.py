"""Source-backed vector figures sized for the final academic poster."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.geometry import geometry_lines
from earthquake_explorer.analysis import select_anchor,case_sample

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final';FIG=OUT/'poster_charts';FIG.mkdir(exist_ok=True)
d=load_verified_snapshot(ROOT);config=json.loads((ROOT/'config.json').read_text())
sections=json.loads((OUT/'sections.json').read_text())
navy='#16364b';blue='#2166ac';gold='#cc8b19';purple='#8e4b98';teal='#167d8d'
colors=[blue,gold,purple];region_colors=[blue,'#b06816',purple,'#57823b','#b14f76','#4b8793','#656565']
names=[r['name'] for r in config['regions']]+['Other']
short=['Japan / Kuril','Indonesia / Philippines','Tonga / Kermadec / Fiji','Andes','Alaska / Aleutians','Mediterranean / Himalaya','Other']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,'axes.labelsize':16,'xtick.labelsize':14,'ytick.labelsize':14,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':navy,'text.color':navy,'xtick.color':navy,'ytick.color':navy,'pdf.fonttype':42,'svg.fonttype':'none'})
def save(fig,name):
    fig.savefig(FIG/(name+'.pdf'),facecolor='white')
    fig.savefig(FIG/(name+'.png'),dpi=200,facecolor='white');plt.close(fig)
def lines(name):
    obj=json.loads((ROOT/'data/raw/geography'/name).read_text(encoding='utf-8'))
    return [np.array([a,b]) for line in geometry_lines(obj) for a,b in zip(line[:-1],line[1:]) if abs(a[0]-b[0])<180]
coast=lines('ne_110m_coastline.geojson');bound=lines('PB2002_boundaries.json')
fig,ax=plt.subplots(figsize=(10,4.9));fig.subplots_adjust(left=.06,right=.98,bottom=.14,top=.90)
ax.set_facecolor('#f4f8fa');ax.add_collection(LineCollection(coast,colors='#85979e',linewidths=.35))
ax.add_collection(LineCollection(bound,colors='#748d98',linewidths=.55))
for c,cls in zip(colors,['Shallow','Intermediate','Deep']):
    p=d[d.depth_class.eq(cls)];ax.scatter(p.longitude,p.latitude,s=1.4,c=c,alpha=.48,rasterized=True,label=cls)
ax.set(xlim=(-180,180),ylim=(-90,90),xticks=[-180,-90,0,90,180],yticks=[-60,0,60],xlabel='Longitude (degrees)',ylabel='Latitude')
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.18),ncol=3,markerscale=5,frameon=False,fontsize=14)
save(fig,'global_map')

fig,ax=plt.subplots(figsize=(10,4));fig.subplots_adjust(left=.12,right=.97,bottom=.23,top=.96)
for i in [5,6]:
    name=names[i]
    v=np.sort(d.loc[d.region.eq(name),'boundary_distance_km']);
    ax.step(v,np.arange(1,len(v)+1)/len(v)*100,where='post',color=region_colors[i],lw=1.8,label=short[i])
v=np.sort(d.boundary_distance_km);ax.step(v,np.arange(1,len(v)+1)/len(v)*100,where='post',color=navy,lw=3,label='All events')
ax.axvline(100,color=navy,ls=':',lw=1);ax.plot(100,100*(v<=100).mean(),'o',c=navy)
ax.text(118,45,'70.15% within 100 km',fontsize=15,fontweight='bold')
ax.set(xlim=(0,500),ylim=(0,101),xlabel='Distance to PB2002 boundary (km)',ylabel='Cumulative share (%)');ax.grid(alpha=.13)
ax.legend(loc='lower right',frameon=False,fontsize=13)
save(fig,'boundary_cdf')

annual=d.groupby('year').size().reindex(range(2000,2026),fill_value=0)
fig,ax=plt.subplots(figsize=(10,3.5));fig.subplots_adjust(left=.12,right=.97,bottom=.26,top=.94)
ax.axvspan(1999.5,2012.5,color=blue,alpha=.055);ax.axvspan(2012.5,2025.5,color=gold,alpha=.09)
ax.plot(annual.index,annual.values,lw=2.4,c=blue,marker='o',ms=4)
ax.hlines([annual.loc[:2012].mean(),annual.loc[2013:].mean()],[2000,2013],[2012,2025],color=navy,ls='--',lw=1.6)
ax.annotate('2011: 2,701',(2011,2701),xytext=(2005,3100),arrowprops={'arrowstyle':'-','color':navy},fontsize=14)
ax.set(xlim=(1999.5,2025.5),ylim=(0,3400),xlabel='UTC year',ylabel='Recorded M ≥ 5 events',xticks=[2000,2005,2010,2015,2020,2025]);ax.grid(axis='y',alpha=.13)
save(fig,'annual')

p=pd.read_csv(ROOT/'docs/temporal_regional_v2/tables/equal_period_comparison.csv')
# Columns are resolved explicitly against the reproducible temporal table below.
part=p[(p.region!='All') & p.threshold.eq(5)].set_index('region').loc[names]
ratecol=next(c for c in p if 'change' in c and 'pct' in c and 'rate' in c)
fig,ax=plt.subplots(figsize=(10,3.9));fig.subplots_adjust(left=.40,right=.89,bottom=.20,top=.98)
vals=part[ratecol].values;ax.barh(short,vals,color=[teal if v>=0 else blue for v in vals],height=.62)
for i,v in enumerate(vals):
    inside=v < -8
    ax.text(v+(1 if v>=0 or inside else -1),i,f'{v:+.1f}%',va='center',ha='left' if v>=0 or inside else 'right',fontsize=14,color='white' if inside else navy)
ax.axvline(0,color=navy,lw=.8);ax.invert_yaxis();ax.set(xlim=(-33,16),xticks=[-30,-15,0,15],xlabel='Exposure-adjusted change (%)');ax.grid(axis='x',alpha=.13);ax.set_axisbelow(True)
save(fig,'regional_change')

fig,ax=plt.subplots(figsize=(10,3.4));fig.subplots_adjust(left=.40,right=.98,bottom=.20,top=.85)
bottom=np.zeros(7)
for cls,c in zip(['Shallow','Intermediate','Deep'],colors):
    vals=np.array([100*d.loc[d.region.eq(n),'depth_class'].eq(cls).mean() for n in names]);ax.barh(short,vals,left=bottom,color=c,label=cls,height=.64);bottom+=vals
ax.invert_yaxis();ax.set(xlim=(0,100),xlabel='Within-region share (%)',xticks=[0,25,50,75,100]);ax.legend(ncol=3,bbox_to_anchor=(1,1.25),loc='upper right',frameon=False,fontsize=14)
save(fig,'depth_shares')

fig,axes=plt.subplots(1,2,figsize=(10,2.6));fig.subplots_adjust(left=.10,right=.99,bottom=.27,top=.84,wspace=.24)
for ax,name in zip(axes,[names[0],names[2]]):
    sec=sections[name];ev=pd.DataFrame(sec['events'],columns=['id','along','offset']).merge(d[['id','depth','depth_class']],on='id',validate='one_to_one')
    for cls,c in zip(['Shallow','Intermediate','Deep'],colors):
        e=ev[ev.depth_class.eq(cls)];ax.scatter(e.along,e.depth,c=c,s=6,alpha=.7,rasterized=True)
    ax.axvline(0,color=navy,ls=':',lw=1);ax.set(xlim=(-200,1200),ylim=(720,-10),xticks=[0,600,1200],yticks=[0,300,600]);ax.set_aspect('equal',adjustable='box')
    ax.set_title(('Northern Tohoku' if name==names[0] else 'Central Tonga')+f' (n={len(ev)})',fontsize=15)
axes[0].set_ylabel('Depth (km)');fig.text(.52,.04,'Along-section distance from trench (km)',ha='center',fontsize=16)
save(fig,'cross_sections')

fig,axes=plt.subplots(1,2,figsize=(10,2.6));fig.subplots_adjust(left=.10,right=.98,bottom=.26,top=.94,wspace=.36)
bins=np.arange(50,97)/10;counts,_=np.histogram(d.mag,bins);axes[0].bar(bins[:-1],counts,width=.095,align='edge',color=blue)
axes[0].set(xlim=(5,9.4),xlabel='Magnitude M',ylabel='Event count',xticks=[5,6,7,8,9]);axes[0].ticklabel_format(axis='y',style='sci',scilimits=(3,3))
threshold=np.sort(d.mag.unique());count=np.array([d.mag.ge(m).sum() for m in threshold]);axes[1].step(threshold,count,where='pre',lw=2.2,c=teal)
axes[1].set(yscale='log',xlabel='Threshold m',ylabel='N(M ≥ m)',xlim=(5,9.4),xticks=[5,6,7,8,9]);axes[1].grid(alpha=.13,which='major')
save(fig,'magnitude')

fig,axes=plt.subplots(3,1,figsize=(10,3.0),sharex=True);fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.97,hspace=.25)
for ax,case,label in zip(axes,config['cases'],['Sumatra 2004','Maule 2010','Tohoku 2011']):
    anchor=select_anchor(d,case);s,stats=case_sample(d,anchor,30,500,2000,2025);counts=np.histogram(s.relative_days,np.arange(-30,31))[0]
    ax.bar(np.arange(-30,30)+.5,counts,width=.92,color=[blue]*30+[gold]*30)
    ax.set(ylim=(0,320),yticks=[0,300],xlim=(-30,30));ax.axvline(0,color=navy,ls=':',lw=.7)
    ax.text(.02,.70,label,transform=ax.transAxes,fontsize=14);ax.text(.98,.70,f"{stats['before_count']} before / {stats['after_count']} after",transform=ax.transAxes,ha='right',fontsize=14)
axes[1].set_ylabel('Events / day');axes[-1].set_xlabel('Days relative to anchor (UTC)')
save(fig,'case_timelines')
print('Saved 8 matching vector-PDF and PNG charts.')
