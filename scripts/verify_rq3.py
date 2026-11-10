"""Independent offline numerical audit; does not import production modules."""
from pathlib import Path
import ast
import hashlib
import json
import re
import numpy as np
import pandas as pd
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
R = 6371.0088
report = {'method': 'Independent haversine, initial bearing, signed along/cross-track formulae; trench intersections solved by scalar brentq on geodesic boundary segments.', 'checks': {}, 'regions': [], 'sections': []}

def check(name, condition, detail=None):
    report['checks'][name] = {'pass': bool(condition), 'detail': detail}

def distance_bearing(start, ends):
    lon1, lat1 = np.deg2rad(start)
    ends = np.atleast_2d(ends)
    lon2, lat2 = np.deg2rad(ends).T
    dl = (lon2 - lon1 + np.pi) % (2*np.pi) - np.pi
    dp = lat2 - lat1
    h = np.sin(dp/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dl/2)**2
    delta = 2*np.arctan2(np.sqrt(np.clip(h,0,1)), np.sqrt(np.clip(1-h,0,1)))
    bearing = np.arctan2(np.sin(dl)*np.cos(lat2), np.cos(lat1)*np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(dl))
    return delta*R, bearing

def destination(start, bearing, km):
    lon1, lat1 = np.deg2rad(start)
    delta = km/R
    lat2 = np.arcsin(np.sin(lat1)*np.cos(delta)+np.cos(lat1)*np.sin(delta)*np.cos(bearing))
    lon2 = lon1 + np.arctan2(np.sin(bearing)*np.sin(delta)*np.cos(lat1), np.cos(delta)-np.sin(lat1)*np.sin(lat2))
    return [float((np.rad2deg(lon2)+180)%360-180), float(np.rad2deg(lat2))]

def project(start, bearing, ends):
    distance, heading = distance_bearing(start, ends)
    delta = distance/R
    along = np.arctan2(np.sin(delta)*np.cos(heading-bearing), np.cos(delta))*R
    left = -np.arcsin(np.clip(np.sin(delta)*np.sin(heading-bearing), -1, 1))*R
    return along, left

config = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
frame = pd.read_csv(ROOT/'data/processed/earthquakes.csv', float_precision='round_trip')
raw = pd.concat([pd.read_csv(p, float_precision='round_trip') for p in sorted((ROOT/'data/raw/usgs').glob('*.csv'))], ignore_index=True)
raw['time'] = pd.to_datetime(raw.time, utc=True, format='mixed')
valid = raw.time.ge('2000-01-01') & raw.time.lt('2026-01-01') & raw.mag.ge(5) & raw.type.eq('earthquake')
check('raw_snapshot_scope', valid.all() and len(raw)==len(frame) and raw.id.is_unique, {'rows': len(raw), 'invalid': int((~valid).sum()), 'duplicates': int(raw.id.duplicated().sum())})
check('processed_raw_ids', set(raw.id)==set(frame.id) and frame.id.is_unique)
raw = raw.set_index('id').loc[frame.id]
for column in ['latitude','longitude','depth','mag']:
    check('processed_raw_'+column, np.array_equal(raw[column].to_numpy(), frame[column].to_numpy(), equal_nan=True))
regions = [box['name'] for box in config['regions']]+['Other']
assigned = []
for row in frame.itertuples():
    assigned.append(next((box['name'] for box in config['regions'] if box['lat'][0] <= row.latitude <= box['lat'][1] and ((box['lon'][0]<=row.longitude<box['lon'][1]) if box['lon'][0]<box['lon'][1] else (row.longitude>=box['lon'][0] or row.longitude<box['lon'][1]))), 'Other'))
check('region_priority', np.array_equal(assigned, frame.region.to_numpy()))
classes = ['Missing' if pd.isna(d) else 'Shallow' if d<70 else 'Intermediate' if d<300 else 'Deep' for d in frame.depth]
check('depth_classes', classes==frame.depth_class.tolist())
check('missing_and_negative', frame.depth.isna().sum()==0 and (frame.depth<0).sum()==4, {'missing': int(frame.depth.isna().sum()), 'negative': int((frame.depth<0).sum()), 'negative_ids': frame.loc[frame.depth<0,'id'].tolist()})
check('processing_seal', hashlib.sha256((ROOT/'data/processed/earthquakes.csv').read_bytes()).hexdigest()==json.loads((ROOT/'data/processed/processing_manifest.json').read_text())['dataset_sha256'])
html = (ROOT/'outputs/final/dashboard.html').read_text(encoding='utf-8')
payload = json.loads(re.search(r'<script id="catalogue" type="application/json">(.*?)</script>',html,re.S).group(1))
rows = payload['rows']
check('embedded_ids_and_order', [r[0] for r in rows]==frame.id.tolist())
check('embedded_config', payload['config']==config and payload['regions']==regions)
check('embedded_classes_and_regions', all(row[8]==['Shallow','Intermediate','Deep','Missing'].index(c) and row[7]==regions.index(reg) for row,c,reg in zip(rows,classes,assigned)))
check('embedded_values', all(r[2]==round(p.latitude,5) and r[3]==round(p.longitude,5) and r[4]==(None if pd.isna(p.depth) else round(p.depth,3)) and r[5]==p.mag for r,p in zip(rows,frame.itertuples())))
count_table = pd.read_csv(ROOT/'outputs/tables/region_depth_counts.csv').set_index('region')
summary_table = pd.read_csv(ROOT/'outputs/tables/regional_summary.csv').set_index('region')
for name in regions:
    part = frame.loc[frame.region.eq(name)]
    depth = part.depth.dropna().to_numpy()
    counts = [int((depth<70).sum()),int(((depth>=70)&(depth<300)).sum()),int((depth>=300).sum())]
    shares = (np.array(counts)/len(depth)*100).tolist()
    q = np.quantile(depth,[.25,.5,.75]).tolist()
    histograms = {}
    for width in [10,20,40]:
        bins = np.arange(-40,720+width,width)
        hist,edges = np.histogram(depth,bins)
        histograms[str(width)] = {'count_sum':int(hist.sum()), 'percent_sum':float((hist/len(depth)*100).sum()), 'bins':len(hist)}
        check(f'{name}_hist_{width}_coverage',hist.sum()==len(depth))
    report['regions'].append({'name':name,'total':len(part),'known':len(depth),'missing':int(part.depth.isna().sum()),'negative':int((depth<0).sum()),'counts':counts,'shares_pct':shares,'q25_median_q75':q,'histograms':histograms})
    check(name+'_count_table', count_table.loc[name,['Shallow','Intermediate','Deep','Missing']].tolist()==counts+[len(part)-len(depth)])
    check(name+'_summary_table', summary_table.loc[name,'count']==len(part) and abs(summary_table.loc[name,'deep_pct_known_depth']-shares[2])<1e-12 and summary_table.loc[name,'median_depth_km']==q[1])

tree = ast.parse((ROOT/'earthquake_explorer/sections.py').read_text(encoding='utf-8'))
presets = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SECTION_PRESETS' for t in node.targets))
boundary = json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text())
for preset in presets:
    name = preset['region']; section=payload['sections'][name]
    ref_a,ref_b = preset['reference_a'],preset['reference_b']
    ref_distance, ref_bearing = distance_bearing(ref_a,[ref_b]); ref_distance=float(ref_distance[0]); ref_bearing=float(ref_bearing[0])
    crossings=[]
    for feature in boundary['features']:
        if feature['properties'].get('Type')!='subduction' or feature['properties'].get('Name') not in preset['boundaries']: continue
        geometry=feature['geometry']; lines=[geometry['coordinates']] if geometry['type']=='LineString' else geometry['coordinates']
        for line in lines:
            for start,end in zip(line[:-1],line[1:]):
                length,bearing=distance_bearing(start,[end]); length=float(length[0]); bearing=float(bearing[0])
                def side(t):
                    return float(project(ref_a,ref_bearing,[destination(start,bearing,length*t)])[1][0])
                f0,f1=side(0),side(1)
                if f0*f1>0: continue
                t=brentq(side,0,1,xtol=1e-14)
                crossing=destination(start,bearing,length*t)
                along,cross=project(ref_a,ref_bearing,[crossing])
                if 0<float(along[0])<ref_distance: crossings.append(crossing)
    distinct=[]
    for crossing in crossings:
        if not any(distance_bearing(crossing,[old])[0][0]<1e-5 for old in distinct): distinct.append(crossing)
    check(name+'_one_trench_crossing',len(distinct)==1,{'crossings':distinct})
    origin=distinct[0]
    _,heading=distance_bearing(origin,[ref_b]); heading=float(heading[0])
    origin_error=float(distance_bearing(origin,[section['origin']])[0][0])
    check(name+'_origin',origin_error<1e-7,{'error_km':origin_error})
    eligible=frame.loc[frame.region.eq(name)&frame.depth.notna()]
    along,cross=project(origin,heading,eligible[['longitude','latitude']].to_numpy())
    selected=(along>=-200-1e-6)&(along<=1200+1e-6)&(abs(cross)<=100+1e-6)
    expected=eligible.loc[selected,'id'].tolist(); actual=[r[0] for r in section['events']]
    check(name+'_section_ids', expected==actual, {'expected':len(expected),'actual':len(actual),'extra':sorted(set(actual)-set(expected)),'missing':sorted(set(expected)-set(actual))})
    selected_depth=eligible.depth.to_numpy()[selected]
    max_along=max(abs(np.array([e[1] for e in section['events']])-along[selected]),default=0)
    max_cross=max(abs(np.array([e[2] for e in section['events']])-cross[selected]),default=0)
    check(name+'_section_coordinates',max_along<=5.01e-7 and max_cross<=5.01e-7,{'max_along_error_km':float(max_along),'max_offset_error_km':float(max_cross)})
    endpoint_along,endpoint_cross=project(origin,heading,[section['a']['coordinates'],section['b']['coordinates']])
    check(name+'_finite_endpoints',np.max(abs(endpoint_along-[-200,1200]))<1e-7 and max(abs(endpoint_cross))<1e-7,{'along_km':endpoint_along.tolist(),'offset_km':endpoint_cross.tolist()})
    sa,sc=project(origin,heading,section['swath'])
    check(name+'_swath_geometry',len(sa)==163 and np.max(abs(abs(sc)-100))<1e-7 and min(sa)>=-200-1e-7 and max(sa)<=1200+1e-7)
    widths=[]
    for width in [50,100,200]:
        mask=(along>=-200-1e-6)&(along<=1200+1e-6)&(abs(cross)<=width+1e-6)
        d=eligible.depth.to_numpy()[mask]
        widths.append({'half_width_km':width,'known':len(d),'shallow':int((d<70).sum()),'intermediate':int(((d>=70)&(d<300)).sum()),'deep':int((d>=300).sum())})
    check(name+'_width_checks',widths==section['width_checks'])
    check(name+'_depth_range',selected_depth.min()>=-10 and selected_depth.max()<=720)
    report['sections'].append({'name':name,'known':len(expected),'counts':[int((selected_depth<70).sum()),int(((selected_depth>=70)&(selected_depth<300)).sum()),int((selected_depth>=300).sum())],'origin':origin,'a':section['a'],'b':section['b'],'origin_error_km':origin_error,'width_checks':widths,'selected_id_sha256':hashlib.sha256('\n'.join(expected).encode()).hexdigest(),'along_min_max':[float(min(along[selected])),float(max(along[selected]))],'offset_min_max':[float(min(cross[selected])),float(max(cross[selected]))]})

report['summary']={'checks':len(report['checks']),'passed':sum(c['pass'] for c in report['checks'].values()),'failed':[name for name,c in report['checks'].items() if not c['pass']], 'dataset_rows':len(frame), 'global_counts':[int((frame.depth<70).sum()),int(((frame.depth>=70)&(frame.depth<300)).sum()),int((frame.depth>=300).sum())]}
target=ROOT/'outputs/final/rq3_independent_verification.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['summary'],ensure_ascii=False))
print('regions: '+json.dumps([{k:r[k] for k in ['name','known','counts','shares_pct','q25_median_q75']} for r in report['regions']],ensure_ascii=False))
print('sections: '+json.dumps([{k:s[k] for k in ['name','known','counts','origin','a','b']} for s in report['sections']],ensure_ascii=False))
raise SystemExit(bool(report['summary']['failed']))
