"""Current four-column poster figures. All values use the sealed catalogue."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.ticker import FuncFormatter
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.geometry import geometry_lines
from earthquake_explorer.analysis import select_anchor,case_sample
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/final';T=O/'tables';F=O/'poster_charts';F.mkdir(exist_ok=True)
d=load_verified_snapshot(ROOT);cfg=json.loads((ROOT/'config.json').read_text());sections=json.loads((O/'sections.json').read_text())
N='#123346';B='#197c9e';G='#d58c27';P='#8254a6';R='#c95d54';C=[B,G,P]
names=[x['name'] for x in cfg['regions']]+['Other'];short=['Japan / Kuril','Indonesia / Phil.','Tonga / Fiji','Andes','Alaska / Aleut.','Med. / Himalaya','Other']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.labelsize':14,'xtick.labelsize':12,'ytick.labelsize':12,'axes.spines.top':False,'axes.spines.right':False,'text.color':N,'axes.labelcolor':N,'xtick.color':N,'ytick.color':N,'pdf.fonttype':42,'axes.titleweight':'bold'})
def save(fig,name):
 fig.savefig(F/(name+'.pdf'),facecolor='white');fig.savefig(F/(name+'.png'),dpi=220,facecolor='white');plt.close(fig)
def chart(h=3.0,left=.14):
 fig,ax=plt.subplots(figsize=(8,h));fig.subplots_adjust(left=left,right=.97,bottom=.24,top=.94);return fig,ax
coast=list(geometry_lines(json.loads((ROOT/'data/raw/geography/ne_110m_coastline.geojson').read_text())))
bounds=list(geometry_lines(json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text())))
fig=plt.figure(figsize=(8,4.2));ax=fig.add_subplot(projection='mollweide');fig.subplots_adjust(left=.04,right=.96,bottom=.08,top=.88);ax.set_facecolor('#edf5f5')
for lines,color,width in [(coast,'#99adb2',.4),(bounds,'#597a84',.65)]:
 for line in lines:
  for piece in np.split(line,np.where(abs(np.diff(line[:,0]))>180)[0]+1):
   if len(piece)>1:ax.plot(np.radians(piece[:,0]),np.radians(piece[:,1]),c=color,lw=width)
for cls,c in zip(['Shallow','Intermediate','Deep'],C):
 q=d[d.depth_class.eq(cls)];ax.scatter(np.radians(q.longitude),np.radians(q.latitude),s=1.4,c=c,alpha=.55,rasterized=True,label=cls)
ax.grid(alpha=.15);ax.set_xticklabels([]);ax.set_yticklabels([]);fig.legend(*ax.get_legend_handles_labels(),ncol=3,loc='upper center',bbox_to_anchor=(.5,.99),frameon=False,markerscale=5,fontsize=12)
save(fig,'global_map')

ref=pd.read_csv(T/'spatial_reference_cdf.csv');fig,ax=chart(3.2)
for col,color,label in [('earthquakes_pct',B,'Earthquakes'),('equal_area_pct',G,'Equal-area globe'),('latitude_matched_pct',P,'Latitude control')]:ax.plot(ref.distance_km,ref[col],c=color,lw=2.6,label=label)
ax.fill_between(ref.distance_km,ref.equal_area_pct,ref.earthquakes_pct,color=B,alpha=.06);ax.axvline(100,c=N,lw=.8,ls=':')
ax.set(xlim=(0,500),ylim=(0,100),xlabel='Nearest PB2002 boundary (km)',ylabel='Cumulative share (%)');ax.legend(loc='center right',bbox_to_anchor=(1,.60),frameon=False,fontsize=12);ax.grid(alpha=.13)
save(fig,'boundary_cdf')

reg=pd.read_csv(T/'regional_summary.csv').set_index('region').loc[names];fig,ax=chart(3.2,.31)
ax.hlines(np.arange(7),0,reg.within_100km_pct,color='#d9e5e8',lw=5);ax.scatter(reg.within_100km_pct,np.arange(7),s=65,c=B,zorder=3)
for i,v in enumerate(reg.within_100km_pct):ax.text(v+2,i,f'{v:.1f}%',va='center',fontsize=12)
ax.set(yticks=range(7),yticklabels=short,xlim=(0,104),xlabel='Events within 100 km (%)');ax.invert_yaxis();ax.grid(axis='x',alpha=.12);save(fig,'regional_proximity')

annual=d.groupby('year').size();fig,ax=chart(3.15)
ax.fill_between(annual.index,annual.values,color=B,alpha=.10);ax.plot(annual.index,annual.values,c=B,lw=2.3,marker='o',ms=3.5)
ax.hlines([annual.loc[:2012].mean(),annual.loc[2013:].mean()],[2000,2013],[2012,2025],color=R,ls='--',lw=1.8)
ax.axvline(2012.5,color=N,lw=.6,ls=':');ax.annotate('2011: 2,701',(2011,2701),xytext=(2003,3070),arrowprops={'arrowstyle':'-','color':N},fontsize=12)
ax.set(xlim=(1999.5,2025.5),ylim=(0,3400),xticks=[2000,2005,2010,2015,2020,2025],xlabel='UTC year',ylabel='M ≥ 5 records');ax.grid(axis='y',alpha=.13);save(fig,'annual')

cmp=pd.read_csv(ROOT/'docs/temporal_regional_v2/tables/equal_period_comparison.csv');q=cmp[cmp.threshold.eq(5)&cmp.region.ne('All')].set_index('region').loc[names];col=next(x for x in q if 'change' in x and 'rate' in x and 'pct' in x)
fig,ax=chart(3.4,.31);vals=q[col].values;ax.barh(short,vals,color=[B if x<0 else R for x in vals],height=.6)
for i,v in enumerate(vals):
 inside=v<-8;ax.text(v+(1 if inside or v>0 else -1),i,f'{v:+.1f}%',color='white' if inside else N,ha='left' if inside or v>0 else 'right',va='center',fontsize=12)
ax.axvline(0,c=N,lw=.8);ax.set(xlim=(-33,17),xlabel='2013–25 vs 2000–12 rate change (%)');ax.invert_yaxis();save(fig,'regional_change')

raw=pd.concat([pd.read_csv(p) for p in (ROOT/'data/raw/usgs').glob('*.csv')]);raw=raw.set_index('id').loc[d.id];years=pd.to_datetime(raw.time,utc=True,format='mixed').dt.year
mw=raw.magType.fillna('').str.lower().str.startswith('mw').groupby(years).mean()*100
fig,ax=chart(3.0);ax.fill_between(mw.index,0,mw.values,color=P,alpha=.8,label='Mw family');ax.fill_between(mw.index,mw.values,100,color='#e6d8ed',label='Other types')
ax.set(ylim=(0,100),xlim=(2000,2025),xlabel='UTC year',ylabel='Share of records (%)',xticks=[2000,2005,2010,2015,2020,2025]);ax.legend(loc='lower left',frameon=False,ncol=2,fontsize=12);save(fig,'magnitude_mix')

fig,ax=chart(3.25,.31);bottom=np.zeros(7)
for cls,c in zip(['Shallow','Intermediate','Deep'],C):
 v=np.array([d.loc[d.region.eq(n),'depth_class'].eq(cls).mean()*100 for n in names]);ax.barh(short,v,left=bottom,color=c,height=.65,label=cls);bottom+=v
ax.set(xlim=(0,100),xlabel='Within-region depth share (%)');ax.invert_yaxis();fig.subplots_adjust(top=.83);fig.legend(*ax.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.60,1),ncol=3,frameon=False,fontsize=10);save(fig,'depth_shares')

fig=plt.figure(figsize=(8,5.3));gs=fig.add_gridspec(2,2,height_ratios=[1.45,1],hspace=.40,wspace=.32);fig.subplots_adjust(left=.10,right=.97,bottom=.15,top=.90)
# Two local route maps retain approximate kilometre aspect at the trench latitude.
for k,name in enumerate([names[0],names[2]]):
 sec=sections[name];lon,lat=sec['origin'];axmap=fig.add_subplot(gs[0,k])
 def unwrap(line):
  points=np.array(line).copy();points[:,0]=lon+(points[:,0]-lon+180)%360-180;return points
 for line in coast:
  line=unwrap(line)
  for piece in np.split(line,np.where(abs(np.diff(line[:,0]))>180)[0]+1):
   if len(piece)>1:axmap.plot(piece[:,0],piece[:,1],c='#9cafb4',lw=.65)
 for line in sec['trench']:
  line=unwrap(line);axmap.plot(line[:,0],line[:,1],color=G,lw=1.3)
 swath=unwrap(sec['swath']);route=unwrap(sec['route']);axmap.fill(swath[:,0],swath[:,1],color=B,alpha=.15);axmap.plot(route[:,0],route[:,1],color=B,lw=1.3)
 axmap.scatter(lon,lat,s=45,marker='*',c=N,zorder=4)
 for label,point in [('A',route[0]),('B',route[-1])]:axmap.annotate(label,point,xytext=(3,5),textcoords='offset points',fontsize=11,color=N,fontweight='bold')
 axmap.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{abs((value+180)%360-180):g}°'+('E' if (value+180)%360-180>=0 else 'W')))
 axmap.yaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{abs(value):g}°'+('N' if value>=0 else 'S')))
 axmap.set(xlim=sec['map_longitude_range'],ylim=sec['map_latitude_range']);axmap.set_aspect(1/np.cos(np.deg2rad(lat)));axmap.tick_params(labelsize=10)
 axmap.set_title(['Japan Trench','Tonga Trench'][k],fontsize=12,pad=4)
 ax=fig.add_subplot(gs[1,k]);ev=pd.DataFrame(sec['events'],columns=['id','along','offset']).merge(d[['id','depth','depth_class']],on='id')
 for cls,c in zip(['Shallow','Intermediate','Deep'],C):
  sub=ev[ev.depth_class.eq(cls)];ax.scatter(sub.along,sub.depth,s=7,c=c,alpha=.7,rasterized=True)
 ax.axvline(0,c=N,lw=.7,ls=':');ax.set(xlim=(-200,1200),ylim=(720,-10),yticks=[0,300,600],xticks=[0,600,1200]);ax.set_aspect('equal',adjustable='box');ax.set_title(['N. Tohoku · n = 351','Central Tonga · n = 640'][k],fontsize=11,pad=4);ax.tick_params(labelsize=10)
 if k==0:ax.set_ylabel('Depth (km)',fontsize=12)
fig.text(.52,.035,'A → B: distance from trench (km)',ha='center',fontsize=12)
save(fig,'cross_sections')

corr=pd.read_csv(T/'spearman_correlations.csv');groups=['All']+names;matrix=np.array([[corr[(corr.group==g)&(corr.x==a)&(corr.y==b)].rho.item() for a,b in [('mag','depth'),('mag','boundary_distance_km'),('depth','boundary_distance_km')]] for g in groups])
fig,ax=plt.subplots(figsize=(8,3.9));fig.subplots_adjust(left=.29,right=.88,bottom=.24,top=.98);im=ax.imshow(matrix,vmin=-1,vmax=1,cmap='RdBu_r',aspect='auto')
for i in range(8):
 for j in range(3):ax.text(j,i,f'{matrix[i,j]:+.2f}',ha='center',va='center',fontsize=12)
ax.set(yticks=range(8),yticklabels=['All']+short,xticks=range(3),xticklabels=['M / depth','M / dist.','Depth / dist.']);ax.tick_params(axis='both',length=0);fig.colorbar(im,ax=ax,fraction=.045,pad=.05,ticks=[-1,0,1],label='Spearman ρ');save(fig,'correlations')

fig,ax=chart(3);m=np.sort(d.mag.unique());v=np.array([d.mag.ge(x).sum() for x in m]);ax.step(m,v,where='pre',color=B,lw=2.6)
for threshold in [5,6,7,8,9]:
 n=int(d.mag.ge(threshold).sum());ax.plot(threshold,n,'o',c=B,ms=5);ax.annotate(f'{n:,}',(threshold,n),xytext=(0,8),textcoords='offset points',ha='center',fontsize=12)
ax.set(yscale='log',xlim=(4.8,9.5),ylim=(.7,180000),xlabel='Magnitude threshold m',ylabel='Events with M ≥ m');ax.grid(alpha=.13);save(fig,'magnitude')

band=pd.read_csv(O/'rq4/tables/magnitude_band_summary.csv');fig,ax=chart(3);x=np.arange(4)
for shift,column,color,label in [(-.18,'count_percent',B,'Event counts'),(.18,'proxy_percent',G,'Summed proxy')]:
 ax.bar(x+shift,band[column],.35,color=color,label=label)
 for a,y in zip(x+shift,band[column]):ax.text(a,y+2,f'{y:.2f}' if y<1 else f'{y:.1f}',ha='center',fontsize=11)
ax.set(xticks=x,xticklabels=['5–<6','6–<7','7–<8','≥8'],ylim=(0,112),xlabel='Magnitude band',ylabel='Share (%)');ax.legend(frameon=False,ncol=2,fontsize=12,loc='upper right');save(fig,'energy_scale')

fig,axes=plt.subplots(3,1,figsize=(8,3.6),sharex=True);fig.subplots_adjust(left=.12,right=.97,top=.97,bottom=.19,hspace=.26)
for ax,case,label in zip(axes,cfg['cases'],['Sumatra 2004','Maule 2010','Tohoku 2011']):
 a=select_anchor(d,case);s,stats=case_sample(d,a,30,500,2000,2025);count=np.histogram(s.relative_days,np.arange(-30,31))[0];ax.bar(np.arange(-30,30)+.5,count,width=.94,color=[B]*30+[G]*30);ax.set(ylim=(0,320),yticks=[0,300],xlim=(-30,30));ax.axvline(0,c=N,ls=':',lw=.6);ax.text(.02,.7,label,transform=ax.transAxes,fontsize=11);ax.text(.98,.7,f"{stats['before_count']} before / {stats['after_count']} after",transform=ax.transAxes,ha='right',fontsize=11)
axes[1].set_ylabel('Events / day');axes[-1].set_xlabel('Days relative to anchor (UTC)');save(fig,'case_timelines')

cum=pd.read_csv(T/'case_cumulative.csv');fig,ax=chart(2.9)
for (name,group),color in zip(cum.groupby('case',sort=False),[B,G,P]):ax.plot(group.day,group.post_cumulative_pct,c=color,lw=2.3,label=name.split()[0])
ax.axvline(3,c=N,ls=':',lw=.8);ax.set(xlim=(0,30),ylim=(0,103),xlabel='Days after anchor',ylabel='Post-window events (%)');ax.legend(loc='lower right',ncol=3,frameon=False,fontsize=11);ax.grid(alpha=.12);save(fig,'case_cumulative')

sens=pd.read_csv(T/'case_window_sensitivity.csv');fig,axes=plt.subplots(1,3,figsize=(8,2.9),sharey=True);fig.subplots_adjust(left=.10,right=.97,bottom=.25,top=.85,wspace=.16)
for ax,(name,g) in zip(axes,sens.groupby('name',sort=False)):
 mat=g.pivot(index='days_each_side',columns='radius_km',values='after_count').loc[[7,30,90],[250,500,1000]].values;im=ax.imshow(mat,cmap='YlGnBu',vmin=0,vmax=sens.after_count.max(),aspect='auto')
 for i in range(3):
  for j in range(3):ax.text(j,i,str(mat[i,j]),ha='center',va='center',fontsize=11,color='white' if mat[i,j]>500 else N)
 ax.set(xticks=range(3),xticklabels=['250','500','1000'],yticks=range(3),yticklabels=['7','30','90']);ax.set_title(name.split()[0],fontsize=12)
axes[0].set_ylabel('Days after');fig.text(.54,.03,'Epicentral radius (km) · post-window counts',ha='center',fontsize=12);save(fig,'window_sensitivity')
print('Generated 14 current scientific figures (PDF + PNG).')
