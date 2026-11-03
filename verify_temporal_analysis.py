"""Independent checks of annual/regional results; no analysis implementation calls."""
import argparse
import calendar
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
VERSION='temporal_regional_v2_20261103'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root=ROOT,output=None):
    root=Path(root);output=Path(output) if output else root/'outputs'/VERSION
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def near(a,b):return abs(a-b)<1e-8 if np.isfinite(a) and np.isfinite(b) else pd.isna(a) and pd.isna(b)
    d=pd.read_csv(root/'data/processed/earthquakes.csv',float_precision='round_trip')
    d.time=pd.to_datetime(d.time,utc=True,format='mixed');years=d.time.dt.year
    provenance=json.loads((output/'provenance.json').read_text(encoding='utf-8'))
    check('dataset snapshot preserved',digest(root/'data/processed/earthquakes.csv')==provenance['dataset_sha256'])
    for path,expected_hash in provenance.get('input_hashes',{}).items():check('input preserved '+path,digest(root/path)==expected_hash)
    old=json.loads((root/'outputs/artifact_manifest.json').read_text(encoding='utf-8'))
    for f in old['files']:check('baseline hash '+f['path'],digest(root/f['path'])==f['sha256'])
    config=json.loads((root/'config.json').read_text(encoding='utf-8'))
    # Independent box assignment, including date-line intervals and priority.
    assigned=[]
    for lon,lat in zip(d.longitude,d.latitude):
        name='Other'
        for box in config['regions']:
            left,right=box['lon'];bottom,top=box['lat']
            inside=(left<=lon<right) if left<right else (lon>=left or lon<right)
            if inside and bottom<=lat<=top:name=box['name'];break
        assigned.append(name)
    check('regional assignment independently reconciles',assigned==d.region.tolist())
    table_dir=output/'tables'
    annual=pd.read_csv(table_dir/'annual_region_threshold.csv')
    regions=['All']+[r['name'] for r in config['regions']]+['Other']
    expected_cells=len(regions)*26*4
    check('annual complete grid',len(annual)==expected_cells and not annual.duplicated(['region','threshold','year']).any())
    for r in annual.itertuples():
        mask=years.eq(r.year)&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))
        n=int(mask.sum());days=365+calendar.isleap(r.year)
        check(f'annual cell {r.region}/{r.threshold}/{r.year}',n==r.count and days==r.exposure_days and near(n*365.2425/days,r.rate_per_365_2425_days))
        denominator=int((years.eq(r.year)&d.mag.ge(r.threshold)).sum())
        check(f'share cell {r.region}/{r.threshold}/{r.year}',near(r.global_share_pct,n/denominator*100 if denominator else np.nan))
        if 2000<r.year<2025:
            counts=[int((years.eq(y)&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))).sum()) for y in [r.year-1,r.year,r.year+1]]
            check(f'smoothing {r.region}/{r.threshold}/{r.year}',near(r.centered_3year_mean,sum(counts)/3))
        else:check(f'no partial smoothing endpoint {r.region}/{r.threshold}/{r.year}',pd.isna(r.centered_3year_mean))
    comp=pd.read_csv(table_dir/'equal_period_comparison.csv')
    for r in comp.itertuples():
        counts=[];days=[]
        for start,end in [(2000,2012),(2013,2025)]:
            count=int((years.between(start,end)&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))).sum())
            counts.append(count);days.append((pd.Timestamp(f'{end+1}-01-01')-pd.Timestamp(f'{start}-01-01')).days)
        check(f'period counts {r.region}/{r.threshold}',counts==[r.early_count,r.late_count] and days==[r.early_days,r.late_days])
        ratio=(counts[1]/days[1])/(counts[0]/days[0]) if counts[0] else np.nan
        check(f'period rate {r.region}/{r.threshold}',near(r.rate_ratio,ratio) and near(r.rate_change_pct,(ratio-1)*100))
        check(f'calendar mean {r.region}/{r.threshold}',near(r.early_annual_mean,counts[0]/13) and near(r.late_annual_mean,counts[1]/13))
    for threshold in [5,5.5,6,7]:
        part=comp.loc[comp.threshold.eq(threshold)];global_row=part.loc[part.region.eq('All')].iloc[0];regions_part=part.loc[part.region.ne('All')]
        check(f'contribution identity {threshold}',near(regions_part.annual_count_difference.sum(),global_row.annual_count_difference))
        check(f'period share sum {threshold}',near(regions_part.early_share_pct.sum(),100) and near(regions_part.late_share_pct.sum(),100))
    slopes=pd.read_csv(table_dir/'descriptive_slopes.csv')
    for r in slopes.itertuples():
        part=annual.loc[annual.region.eq(r.region)&annual.threshold.eq(r.threshold)].sort_values('year')
        xs,ys=part.year.tolist(),part['count'].tolist()
        calculate=lambda indices:np.median([(ys[j]-ys[i])/(xs[j]-xs[i]) for i in indices for j in indices if j>i])
        check(f'Sen slope {r.region}/{r.threshold}',near(r.sen_slope_events_per_year,calculate(list(range(26)))))
        omitted=[calculate([i for i in range(26) if i!=omit]) for omit in range(26)]
        check(f'omitted-year range {r.region}/{r.threshold}',near(min(omitted),r.leave_one_year_out_min) and near(max(omitted),r.leave_one_year_out_max))
    batches=[pd.read_csv(root/f'data/raw/usgs/{y}.csv') for y in range(2000,2026)]
    raw=pd.concat(batches,ignore_index=True);raw.updated=pd.to_datetime(raw.updated,utc=True,format='mixed')
    raw=raw.sort_values('updated',kind='stable',na_position='first').drop_duplicates('id',keep='last').set_index('id').loc[d.id].reset_index()
    check('raw metadata join grain',raw.id.tolist()==d.id.tolist())
    profile=pd.read_csv(table_dir/'annual_reporting_profile.csv')
    fields=['nst','gap','dmin','rms','horizontalError','depthError','magError','magNst']
    for r in profile.itertuples():
        mask=years.eq(r.year)&(True if r.region=='All' else d.region.eq(r.region));part=d.loc[mask];meta=raw.loc[mask.to_numpy()]
        check(f'profile denominator {r.region}/{r.year}',len(part)==r.n)
        values={'mw_prefix_pct':part.magType.fillna('').str.lower().str.startswith('mw').mean()*100,
            'depth_10km_pct':part.depth.eq(10).mean()*100,'depth_33km_pct':part.depth.eq(33).mean()*100,
            'automatic_pct':part.status.fillna('').str.lower().eq('automatic').mean()*100}
        for col in fields:values[col+'_available_pct']=np.isfinite(pd.to_numeric(meta[col],errors='coerce')).mean()*100
        check(f'profile values {r.region}/{r.year}',all(near(value,getattr(r,col)) for col,value in values.items()))
    for name,column in [('annual_magnitude_type_mix','magType'),('annual_network_mix','net')]:
        mix=pd.read_csv(table_dir/(name+'.csv'));base=(d[column] if column in d else raw[column]).fillna('Missing').astype(str).str.strip().str.lower().replace('','missing')
        expected=pd.crosstab(years,base)
        check(name+' count reconciliation',all(int(expected.loc[r.year,getattr(r,column)])==r.count for r in mix.itertuples()) and int(mix['count'].sum())==len(d))
        check(name+' share reconciliation',all(near(r.share_pct,r.count/int(years.eq(r.year).sum())*100) for r in mix.itertuples()))
    period_quality=pd.read_csv(table_dir/'period_reporting_comparison.csv')
    for r,(start,end) in zip(period_quality.itertuples(),[(2000,2012),(2013,2025)]):
        mask=years.between(start,end);part=d.loc[mask];meta=raw.loc[mask.to_numpy()]
        expected={'mw_prefix_pct':part.magType.fillna('').str.lower().str.startswith('mw').mean()*100,
            'depth_10km_pct':part.depth.eq(10).mean()*100,'depth_33km_pct':part.depth.eq(33).mean()*100,
            'automatic_pct':part.status.fillna('').str.lower().eq('automatic').mean()*100,
            **{c+'_available_pct':np.isfinite(pd.to_numeric(meta[c],errors='coerce')).mean()*100 for c in fields}}
        check('period reporting weighted by events '+r.period,r.n==len(part) and all(near(v,getattr(r,k)) for k,v in expected.items()))
    removed_ids=set()
    anchors=d.loc[d.mag.ge(8)]
    for anchor in anchors.itertuples():
        delta=(d.time-anchor.time).dt.total_seconds()
        p=np.deg2rad(d.latitude.to_numpy());q=np.deg2rad(anchor.latitude);delta_lon=np.deg2rad(d.longitude.to_numpy()-anchor.longitude)
        h=np.sin((p-q)/2)**2+np.cos(p)*np.cos(q)*np.sin(delta_lon/2)**2
        distance=2*6371.0088*np.arctan2(np.sqrt(np.clip(h,0,1)),np.sqrt(np.clip(1-h,0,1)))
        mask=delta.ge(0)&delta.lt(30*86400)&(distance<=500)
        removed_ids.update(d.loc[mask,'id'])
    reduced=pd.read_csv(table_dir/'window_removal_annual.csv')
    for r in reduced.itertuples():
        count=int((~d.id.isin(removed_ids)&years.eq(r.year)&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))).sum())
        check(f'window union {r.region}/{r.threshold}/{r.year}',count==r.count)
    summary=json.loads((table_dir/'summary.json').read_text(encoding='utf-8'))
    check('window summary union',summary['sequence_sensitivity']['removed_unique_events']==len(removed_ids) and summary['sequence_sensitivity']['anchors']==len(anchors))
    selection=pd.read_csv(table_dir/'selection_sensitivity.csv')
    masks={'All preferred types':np.ones(len(d),dtype=bool),'mw-prefix types':d.magType.fillna('').str.lower().str.startswith('mw'),
        'Reviewed only':d.status.fillna('').str.lower().eq('reviewed'),'Outside M8+ windows':~d.id.isin(removed_ids)}
    for r in selection.itertuples():
        mask=masks[r.selection]&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))
        n0=int((mask&years.le(2012)).sum());n1=int((mask&years.ge(2013)).sum())
        ratio=n1/4748/(n0/4749) if n0 else np.nan
        check(f'selection {r.selection}/{r.region}/{r.threshold}',[n0,n1]==[r.early_count,r.late_count] and near(r.rate_ratio,ratio))
    boxes=pd.read_csv(table_dir/'region_box_period_sensitivity.csv')
    for expansion in [-2,0,2]:
        names=np.full(len(d),'Other',dtype=object);lon=d.longitude.to_numpy();lat=d.latitude.to_numpy()
        for box in config['regions']:
            left=(box['lon'][0]-expansion+180)%360-180;right=(box['lon'][1]+expansion+180)%360-180
            bottom=max(-90,box['lat'][0]-expansion);top=min(90,box['lat'][1]+expansion)
            inside=((lon>=left)&(lon<right)) if left<right else ((lon>=left)|(lon<right))
            names[(names=='Other')&inside&(lat>=bottom)&(lat<=top)]=box['name']
        for r in boxes.loc[boxes.expansion_degrees.eq(expansion)].itertuples():
            mask=d.mag.ge(r.threshold)&(True if r.region=='All' else names==r.region)
            n0=int((mask&years.le(2012)).sum());n1=int((mask&years.ge(2013)).sum())
            ratio=n1/4748/(n0/4749) if n0 else np.nan
            check(f'box sensitivity {expansion}/{r.region}/{r.threshold}',[n0,n1]==[r.early_count,r.late_count] and near(r.rate_ratio,ratio))
    coverage=pd.read_csv(table_dir/'source_batch_coverage.csv')
    for r,batch in zip(coverage.itertuples(),batches):
        timestamp=pd.to_datetime(batch.time,utc=True,format='mixed')
        check('source partition '+str(r.year),r.source_rows==len(batch) and r.source_columns==len(batch.columns)
            and r.unique_ids_inside_calendar_year==batch.loc[timestamp.dt.year.eq(r.year),'id'].nunique()
            and r.retained_events==int(years.eq(r.year).sum()) and r.source_sha256==digest(root/f'data/raw/usgs/{r.year}.csv'))
    monthly=pd.read_csv(table_dir/'monthly_coverage.csv');expected=d.groupby(d.time.dt.strftime('%Y-%m')).size()
    check('all 312 calendar months',len(monthly)==312 and all(expected.get(r.month,0)==r.count for r in monthly.itertuples()))
    blocks=pd.read_csv(table_dir/'multiyear_blocks.csv')
    for r in blocks.itertuples():
        start,end=map(int,r.period.split('–'))
        count=int((years.between(start,end)&d.mag.ge(r.threshold)&(True if r.region=='All' else d.region.eq(r.region))).sum())
        check(f'block {r.region}/{r.threshold}/{r.period}',count==r.count and near(r.annual_mean,count/(end-start+1)))
    manifest=json.loads((output/'artifact_manifest.json').read_text(encoding='utf-8'))
    for f in manifest['files']:check('extension hash '+f['path'],digest(output/f['path'])==f['sha256'])
    check('nine new figures',len(list((output/'figures').glob('*.png')))==9)
    public=root/'docs/temporal_regional_v2'
    if public.exists():
        manifest_pub=json.loads((public/'artifact_manifest.json').read_text(encoding='utf-8'))
        check('public excludes local event-level window rows',not (public/'tables/sequence_windows.csv').exists())
        for f in manifest_pub['files']:
            check('public copy '+f['path'],digest(public/f['path'])==f['sha256'] and digest(output/f['path'])==f['sha256'])
    result={'status':'PASS','checks_passed':len(checks),'events':len(d),'new_figures':9,'baseline_files_preserved':len(old['files']),
        'dataset_sha256':digest(root/'data/processed/earthquakes.csv'),'sequence_removed_unique':len(removed_ids),'checks':checks}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args();verify(args.root)
