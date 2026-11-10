"""Independent numerical audit of the proposal-2.0 extension (read-only inputs)."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.stats import qmc,spearmanr
from scipy.spatial import cKDTree
from verify_results import dense_boundary_nodes
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/final';T=O/'tables'
checks=[]
def check(name,ok):
    assert bool(ok),name
    checks.append(name)
d=pd.read_csv(ROOT/'data/processed/earthquakes.csv',float_precision='round_trip');d.time=pd.to_datetime(d.time,utc=True,format='mixed')
check('canonical hash',hashlib.sha256((ROOT/'data/processed/earthquakes.csv').read_bytes()).hexdigest()=='231b5b4fadf2d0d4eccfe4f03b8eb8489d225ff84e921f18d2b973af46d544ff')
facts=json.loads((O/'expanded_facts.json').read_text());cache=np.load(O/'reference_cache.npz')
binding=hashlib.sha256(b''.join((ROOT/p).read_bytes() for p in ['data/raw/geography/PB2002_boundaries.json','earthquake_explorer/geometry.py','earthquake_explorer/spatial_reference.py','data/processed/earthquakes.csv'])+json.dumps(facts['sampling_spec'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
check('reference cache binding',str(cache['binding'])==binding==facts['binding_sha256'])
area=np.concatenate([cache[f'area_{seed}'] for seed in range(5002,5006)])
check('reference size',len(area)==65536 and len(cache['latitude'])==16384)
check('finite nonnegative distances',np.isfinite(area).all() and (area>=0).all())
cdf=pd.read_csv(T/'spatial_reference_cdf.csv')
for col,values in [('earthquakes_pct',d.boundary_distance_km.values),('equal_area_pct',area),('latitude_matched_pct',cache['latitude'])]:
    expected=np.array([(values<=x).mean()*100 for x in cdf.distance_km]);check('CDF '+col,np.allclose(cdf[col],expected,atol=1e-10))
for row in pd.read_csv(T/'spatial_reference_summary.csv').itertuples():
    check(f'threshold {row.radius_km}',np.allclose([row.observed_pct,row.equal_area_pct,row.latitude_matched_pct,row.observed_to_area_ratio],[(d.boundary_distance_km<=row.radius_km).mean()*100,(area<=row.radius_km).mean()*100,(cache['latitude']<=row.radius_km).mean()*100,(d.boundary_distance_km<=row.radius_km).mean()/(area<=row.radius_km).mean()]))
# An independent <=1 km dense-node spherical oracle bounds exact-arc distances.
nodes=dense_boundary_nodes(json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text()));tree=cKDTree(nodes);gaps=[]
for seed in [5002,5003,5004,5005,5012]:
    u=qmc.Sobol(d=2,scramble=True,seed=seed).random_base2(14);lon=(360*u[:,0]-180)*np.pi/180
    if seed==5012:lat=np.sort(d.latitude.values)[np.minimum((u[:,1]*len(d)).astype(int),len(d)-1)]*np.pi/180;key='latitude'
    else:lat=np.arcsin(2*u[:,1]-1);key=f'area_{seed}'
    idx=np.random.default_rng(seed+100).choice(len(u),128,replace=False)
    v=np.column_stack([np.cos(lat[idx])*np.cos(lon[idx]),np.cos(lat[idx])*np.sin(lon[idx]),np.sin(lat[idx])])
    chord,_=tree.query(v);upper=2*6371.0088*np.arcsin(np.clip(chord/2,0,1));gap=upper-cache[key][idx];gaps.extend(gap)
    check('independent arc bound '+key,(gap>=-1e-5).all() and (gap<=.501).all())
bands=pd.read_csv(O/'rq4/tables/magnitude_band_summary.csv')
for i,(lo,hi) in enumerate([(5,6),(6,7),(7,8),(8,10)]):
    mask=d.mag.ge(lo)&d.mag.lt(hi);proxy=10**(1.5*(d.mag-5))
    check('energy and counts '+str(lo),np.allclose([bands.iloc[i]['n'],bands.iloc[i].count_percent,bands.iloc[i].proxy_percent],[mask.sum(),mask.mean()*100,proxy[mask].sum()/proxy.sum()*100],atol=1e-7))
corr=pd.read_csv(T/'spearman_correlations.csv')
for r in corr.itertuples():
    if r.group!='All' and r.group not in set(d.region):continue
    q=d if r.group=='All' else d[d.region.eq(r.group)]
    check('Spearman '+r.group+' '+r.x+' '+r.y,np.isclose(r.rho,spearmanr(q[r.x],q[r.y],nan_policy='omit').statistic))
cum=pd.read_csv(T/'case_cumulative.csv');sens=pd.read_csv(T/'case_window_sensitivity.csv')
for name,g in sens.groupby('name'):
    anchor=d[d.id.eq(g.iloc[0].anchor_id)].iloc[0];delta=(d.time-anchor.time).dt.total_seconds()/86400
    lat1,lat2=np.deg2rad(d.latitude),np.deg2rad(anchor.latitude);dlon=np.deg2rad(d.longitude-anchor.longitude)
    hav=np.sin((lat1-lat2)/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2;km=2*6371.0088*np.arcsin(np.sqrt(np.clip(hav,0,1)))
    for r in g.itertuples():
        eligible=(km<=r.radius_km)&d.id.ne(anchor.id);before=(eligible&delta.ge(-r.days_each_side)&delta.lt(0)).sum();after=(eligible&delta.ge(0)&delta.lt(r.days_each_side)).sum()
        check(f'case window {name} {r.radius_km} {r.days_each_side}',before==r.before_count and after==r.after_count)
    post=(km<=500)&d.id.ne(anchor.id)&delta.ge(0)&delta.lt(30)
    for r in cum[cum.case.eq(name)].itertuples():
        n=int((post&delta.lt(r.day)).sum());check(f'cumulative {name} {r.day}',r.post_total==post.sum() and r.post_cumulative_n==n and np.isclose(r.post_cumulative_pct,100*n/post.sum()))
report={'status':'PASS','checks_passed':len(checks),'checks':checks,'independent_geometry':{'reference_points':640,'dense_nodes':len(nodes),'spacing_km':1,'max_upper_bound_gap_km':float(max(gaps))},'dataset_sha256':hashlib.sha256((ROOT/'data/processed/earthquakes.csv').read_bytes()).hexdigest()}
(O/'expansion_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
