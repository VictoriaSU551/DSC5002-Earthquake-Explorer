"""Restore useful proposal-2.0 methods to the verified proposal-3.0 experiment."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import scipy
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.geometry import nearest_boundary_km
from earthquake_explorer.spatial_reference import sphere_reference,latitude_reference
from earthquake_explorer.analysis import select_anchor,case_sample
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final';T=OUT/'tables'
d=load_verified_snapshot(ROOT);config=json.loads((ROOT/'config.json').read_text());boundary=json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text())
spec={'power':14,'area_seeds':[5002,5003,5004,5005],'latitude_seed':5012,'scipy':scipy.__version__,'numpy':np.__version__}
spec_json=json.dumps(spec,sort_keys=True,separators=(',',':'))
cache=OUT/'reference_cache.npz';binding=hashlib.sha256((ROOT/'data/raw/geography/PB2002_boundaries.json').read_bytes()+(ROOT/'earthquake_explorer/geometry.py').read_bytes()+(ROOT/'earthquake_explorer/spatial_reference.py').read_bytes()+(ROOT/'data/processed/earthquakes.csv').read_bytes()+spec_json.encode()).hexdigest()
expected={f'area_{s}' for s in spec['area_seeds']}|{'latitude'}
distances=None
if cache.exists():
    with np.load(cache) as saved:
        valid=str(saved['binding'])==binding and set(saved.files)==expected|{'binding'}
        if valid and all(saved[k].shape==(2**spec['power'],) and np.isfinite(saved[k]).all() and (saved[k]>=0).all() for k in expected):
            distances={k:saved[k] for k in expected}
if distances is None:
    distances={}
    for seed in spec['area_seeds']:
        lon,lat=sphere_reference(spec['power'],seed);distances[f'area_{seed}']=nearest_boundary_km(lon,lat,boundary)
        print('Computed equal-area reference',seed,flush=True)
    lon,lat=latitude_reference(d.latitude,spec['power'],spec['latitude_seed']);distances['latitude']=nearest_boundary_km(lon,lat,boundary)
    np.savez_compressed(cache,binding=binding,**distances)
area=np.concatenate([v for k,v in distances.items() if k.startswith('area_')])
observed=d.boundary_distance_km.to_numpy();grid=np.arange(0,5001,10)
pd.DataFrame({'distance_km':grid,'earthquakes_pct':np.searchsorted(np.sort(observed),grid,side='right')/len(observed)*100,'equal_area_pct':np.searchsorted(np.sort(area),grid,side='right')/len(area)*100,'latitude_matched_pct':np.searchsorted(np.sort(distances['latitude']),grid,side='right')/len(distances['latitude'])*100}).to_csv(T/'spatial_reference_cdf.csv',index=False)
rows=[]
for threshold in [50,100,200,500]:
    obs=float((observed<=threshold).mean()*100);ref=float((area<=threshold).mean()*100)
    reps=[float((v<=threshold).mean()*100) for k,v in distances.items() if k.startswith('area_')]
    rows.append({'radius_km':threshold,'observed_pct':obs,'equal_area_pct':ref,'latitude_matched_pct':float((distances['latitude']<=threshold).mean()*100),'observed_to_area_ratio':obs/ref,'replicate_min_pct':min(reps),'replicate_max_pct':max(reps)})
pd.DataFrame(rows).to_csv(T/'spatial_reference_summary.csv',index=False)
time_rows=[]
for case in config['cases']:
    a=select_anchor(d,case);s,stats=case_sample(d,a,30,500,2000,2025);after=s[s.relative_days.ge(0)]
    for day in range(31):time_rows.append({'case':case['name'],'day':day,'post_cumulative_n':int(after.relative_days.lt(day).sum()),'post_total':len(after),'post_cumulative_pct':100*after.relative_days.lt(day).mean()})
pd.DataFrame(time_rows).to_csv(T/'case_cumulative.csv',index=False)
by_depth=d.groupby('depth_class').agg(n=('id','size'),median_distance_km=('boundary_distance_km','median'),median_magnitude=('mag','median')).reset_index()
by_depth.to_csv(T/'depth_distance_summary.csv',index=False)
result={'design':'4 independent scrambled Sobol equal-area spherical designs, 16384 points each; lon uniform, sin(latitude) uniform; whole globe including ocean. Latitude control preserves empirical latitude distribution and randomizes longitude. Both are descriptive geographic references, not realistic seismicity null models.','reference_n':len(area),'latitude_control_n':len(distances['latitude']),'seeds':[5002,5003,5004,5005,5012],'radius_km':6371.0088,'thresholds':rows,'median_area_distance_km':float(np.median(area)),'replicate_note':'Across-design range is numerical sensitivity, not a confidence interval. No p-value or causal enrichment claim.','binding_sha256':binding}
result['sampling_spec']=spec
result['seeds']=spec['area_seeds']+[spec['latitude_seed']]
result['design']=f"{len(spec['area_seeds'])} independent scrambled Sobol equal-area spherical designs, {2**spec['power']} points each; longitude uniform and sine(latitude) uniform; whole globe including oceans. Latitude control uses empirical latitude quantiles and uniform longitude. Descriptive geographic references, not realistic seismicity null models."
(OUT/'expanded_facts.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert len(area)==len(spec['area_seeds'])*2**spec['power'] and np.isfinite(area).all() and (area>=0).all()
print(json.dumps(result,indent=2))
