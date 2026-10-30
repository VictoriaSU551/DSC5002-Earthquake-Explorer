"""Independent checks of the downloaded inputs, output counts and geometry.

This script does not call the pipeline's cleaning or spatial functions.
The spherical distance oracle samples PB2002 arcs at <=1 km spacing;
the nearest sample is an upper bound within <=0.5 km of a true segment minimum.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dense_boundary_nodes(layer,spacing_km=1):
    nodes=[]
    for f in layer['features']:
        lines=[f['geometry']['coordinates']] if f['geometry']['type']=='LineString' else f['geometry']['coordinates']
        for line in lines:
            coords=np.deg2rad(np.asarray(line))
            lon,lat=coords[:,0],coords[:,1]
            v=np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
            for a,b in zip(v[:-1],v[1:]):
                angle=math.acos(float(np.clip(a@b,-1,1)))
                if angle<1e-10:
                    nodes.append(a[None,:]);continue
                count=max(1,math.ceil(angle*6371.0088/spacing_km))
                t=np.linspace(0,1,count+1)
                nodes.append((np.sin((1-t)*angle)[:,None]*a+np.sin(t*angle)[:,None]*b)/math.sin(angle))
    return np.concatenate(nodes)


def main():
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    source=json.loads((ROOT/'data/sources.lock.json').read_text(encoding='utf-8'))
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    for item in source['files']:
        check('source hash '+item['file'],digest(ROOT/item['file'])==item['sha256'])
    count_path=ROOT/'data/raw/catalog_count.txt'
    check('count receipt hash',digest(count_path)==source['count_receipt']['sha256'])
    check('count receipt value',int(count_path.read_text())==source['source_count'])
    raw=pd.concat([pd.read_csv(ROOT/f'data/raw/usgs/{y}.csv') for y in range(config['start_year'],config['end_year']+1)],ignore_index=True)
    times=pd.to_datetime(raw.time,utc=True,format='mixed')
    keep=times.ge(pd.Timestamp(f"{config['start_year']}-01-01",tz='UTC')) & times.lt(pd.Timestamp(f"{config['end_year']+1}-01-01",tz='UTC'))
    check('raw unique count',raw.loc[keep,'id'].nunique()==source['source_count'])
    data=pd.read_csv(ROOT/'data/processed/earthquakes.csv')
    data.time=pd.to_datetime(data.time,utc=True,format='mixed')
    check('dataset ID uniqueness',data.id.is_unique)
    check('coordinate range',bool(data.latitude.between(-90,90).all() and data.longitude.between(-180,180).all()))
    check('magnitude threshold',bool(data.mag.ge(config['min_magnitude']).all()))
    check('retained IDs are source IDs',set(data.id)<=set(raw.id))
    source_by_id=raw.drop_duplicates('id',keep='last').set_index('id')
    for col in ['latitude','longitude','depth','mag']:
        check('source values preserved '+col,bool(np.allclose(data[col],source_by_id.loc[data.id,col],equal_nan=True,rtol=1e-8,atol=1e-7)))
    s=json.loads((ROOT/'outputs/tables/summary.json').read_text())
    check('summary event count',s['n_events']==len(data))
    annual=pd.read_csv(ROOT/'outputs/tables/annual_counts.csv',index_col=0)['count']
    actual=data.groupby(data.time.dt.year).size().reindex(annual.index,fill_value=0)
    check('annual counts independently reconcile',annual.tolist()==actual.tolist() and int(annual.sum())==len(data))
    regions=pd.read_csv(ROOT/'outputs/tables/region_year_counts.csv',index_col=0)
    check('region-year counts partition data',int(regions.to_numpy().sum())==len(data))
    depths=pd.read_csv(ROOT/'outputs/tables/region_depth_counts.csv',index_col=0)
    check('depth classes partition data',int(depths.to_numpy().sum())==len(data))
    check('depth cutoff counts',s['depth_counts']['Deep']==int(data.depth.ge(300).sum()) and s['depth_counts']['Shallow']==int(data.depth.lt(70).sum()))
    for km,pct in s['within_boundary_km_pct'].items():
        check('boundary percentage '+km,abs(pct-data.boundary_distance_km.le(float(km)).mean()*100)<1e-6)
    frequency=pd.read_csv(ROOT/'outputs/tables/magnitude_frequency.csv')
    check('survival counts independently reconcile',all(int(row.cumulative_count)==int(data.mag.ge(row.magnitude-1e-10).sum()) for row in frequency.itertuples()))
    for case in s['cases']:
        anchor=data.loc[data.id.eq(case['anchor_id'])].iloc[0]
        delta=(data.time-anchor.time).dt.total_seconds()/86400
        lat1,lat2=np.deg2rad(data.latitude.to_numpy()),math.radians(anchor.latitude)
        dlon=np.deg2rad(data.longitude.to_numpy()-anchor.longitude)
        h=np.sin((lat1-lat2)/2)**2+np.cos(lat1)*math.cos(lat2)*np.sin(dlon/2)**2
        distance=2*6371.0088*np.arctan2(np.sqrt(np.clip(h,0,1)),np.sqrt(np.clip(1-h,0,1)))
        mask=(distance<=case['radius_km'])&delta.ge(-case['days_each_side'])&delta.lt(case['days_each_side'])&data.id.ne(anchor.id)
        check('case before '+case['name'],int((mask&delta.lt(0)).sum())==case['before_count'])
        check('case after '+case['name'],int((mask&delta.ge(0)).sum())==case['after_count'])
        date=anchor.time.strftime('%Y-%m-%d')
        members=pd.read_csv(ROOT/f'outputs/tables/case_{date}_events.csv')
        check('case membership '+case['name'],set(members.id)==set(data.loc[mask,'id']))
    layer=json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text())
    nodes=dense_boundary_nodes(layer)
    tree=cKDTree(nodes)
    sampled=data.sample(min(256,len(data)),random_state=5002)
    lat,lon=np.deg2rad(sampled.latitude),np.deg2rad(sampled.longitude)
    vectors=np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
    chord,_=tree.query(vectors)
    approx=2*6371.0088*np.arcsin(np.clip(chord/2,0,1))
    differences=approx-sampled.boundary_distance_km.to_numpy()
    check('spatial independent dense-node upper bound',bool(np.all(differences>=-1e-5)))
    check('spatial independent 0.501 km error bound',bool(np.all(differences<=.501)))
    manifest=json.loads((ROOT/'outputs/artifact_manifest.json').read_text())
    for item in manifest['files']:check('artifact hash '+item['path'],digest(ROOT/item['path'])==item['sha256'])
    figures=list((ROOT/'outputs/figures').glob('*.png'))
    check('twelve figures produced',len(figures)==12)
    check('substantive figures',all(p.stat().st_size>15000 for p in figures))
    report={'status':'PASS','checks_passed':len(checks),'checks':checks,'events':len(data),
            'boundary_validation':{'sample_events':len(sampled),'dense_nodes':len(nodes),'spacing_km':1,
                'maximum_upper_bound_gap_km':float(differences.max()),'minimum_upper_bound_gap_km':float(differences.min())},
            'dataset_sha256':digest(ROOT/'data/processed/earthquakes.csv')}
    (ROOT/'outputs/verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
