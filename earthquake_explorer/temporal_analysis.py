"""Versioned annual/regional analysis of a fixed, thresholded catalogue.

All rates are recorded-event counts per time exposure, not hazard estimates.
No independent-event p-values, completeness correction or causal claim is made.
"""
import calendar
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .geometry import epicentral_distance_km
from .prepare import assign_regions
from .temporal_utils import write_json

VERSION = 'temporal_regional_v2_20261103'
THRESHOLDS = (5., 5.5, 6., 7.)
QUALITY_FIELDS = ['nst','gap','dmin','rms','horizontalError','depthError','magError','magNst']


def equal_periods(start_year,end_year):
    years=end_year-start_year+1
    if years<2 or years%2:
        raise ValueError('Equal-period analysis requires an even number of complete calendar years')
    split=start_year+years//2
    return [(start_year,split-1),(split,end_year)]


def annual_panel(frame,config,thresholds=THRESHOLDS):
    years=list(range(config['start_year'],config['end_year']+1))
    regions=[r['name'] for r in config['regions']]+['Other']
    if frame.id.duplicated().any():raise ValueError('Annual analysis requires one row per event ID')
    if not set(frame.region)<=set(regions):raise ValueError('Unknown region in analysis data')
    records=[]
    for threshold in thresholds:
        subset=frame.loc[frame.mag.ge(threshold)]
        global_counts=subset.groupby('year').size().reindex(years,fill_value=0)
        for region in ['All']+regions:
            part=subset if region=='All' else subset.loc[subset.region.eq(region)]
            counts=part.groupby('year').size().reindex(years,fill_value=0)
            smooth=counts.rolling(3,center=True,min_periods=3).mean()
            for year in years:
                count=int(counts.loc[year]);days=366 if calendar.isleap(year) else 365
                records.append({'region':region,'threshold':threshold,'year':year,'count':count,
                    'exposure_days':days,'rate_per_365_2425_days':count*365.2425/days,
                    'global_share_pct':count/global_counts.loc[year]*100 if global_counts.loc[year] else np.nan,
                    'centered_3year_mean':smooth.loc[year]})
    return pd.DataFrame(records)


def compare_periods(annual,periods):
    records=[]
    for (region,threshold),group in annual.groupby(['region','threshold'],sort=False):
        result={'region':region,'threshold':threshold}
        for label,(start,end) in zip(['early','late'],periods):
            part=group.loc[group.year.between(start,end)]
            count=int(part['count'].sum());days=int(part.exposure_days.sum())
            if len(part)!=end-start+1:raise ValueError('Annual panel is missing a complete year')
            result.update({label+'_period':f'{start}–{end}',label+'_count':count,label+'_days':days,
                label+'_annual_mean':count/(end-start+1),label+'_rate':count*365.2425/days})
        result['rate_ratio']=result['late_rate']/result['early_rate'] if result['early_rate'] else np.nan
        result['rate_change_pct']=(result['rate_ratio']-1)*100
        result['annual_count_difference']=result['late_annual_mean']-result['early_annual_mean']
        result['small_period_count']=min(result['early_count'],result['late_count'])<30
        records.append(result)
    out=pd.DataFrame(records)
    for threshold in out.threshold.unique():
        global_row=out.loc[out.region.eq('All')&out.threshold.eq(threshold)].iloc[0]
        for period in ['early','late']:
            out.loc[out.threshold.eq(threshold),period+'_share_pct']=out.loc[out.threshold.eq(threshold),period+'_count']/global_row[period+'_count']*100 if global_row[period+'_count'] else np.nan
    out['share_change_pp']=out.late_share_pct-out.early_share_pct
    return out


def join_reporting_metadata(frame,raw):
    if not frame.id.is_unique:raise ValueError('Analysis event IDs are not unique')
    raw=raw.copy()
    if 'updated' in raw:
        raw['updated']=pd.to_datetime(raw.updated,utc=True,errors='coerce',format='mixed')
        raw=raw.sort_values('updated',kind='stable',na_position='first')
    raw=raw.drop_duplicates('id',keep='last')
    columns=QUALITY_FIELDS+['net','locationSource','magSource']
    for col in columns:
        if col not in raw:raw[col]=np.nan
    joined=frame.merge(raw[['id']+columns],on='id',how='left',validate='one_to_one',indicator=True)
    if not joined['_merge'].eq('both').all():raise ValueError('Analysis IDs missing from source metadata')
    joined=joined.drop(columns='_merge')
    for col in QUALITY_FIELDS:
        joined[col]=pd.to_numeric(joined[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
    return joined


def sen_slope(years,counts):
    x,y=np.asarray(years,dtype=float),np.asarray(counts,dtype=float)
    if len(x)<2:return None
    i,j=np.triu_indices(len(x),1)
    distinct=x[j]!=x[i]
    return float(np.median((y[j[distinct]]-y[i[distinct]])/(x[j[distinct]]-x[i[distinct]]))) if distinct.any() else None


def sequence_window_mask(frame,days=30,radius_km=500,study_bounds=None):
    removed=np.zeros(len(frame),dtype=bool)
    anchors=[]
    for anchor in frame.loc[frame.mag.ge(8)].itertuples():
        delta=(frame.time-anchor.time).dt.total_seconds()/86400
        distance=epicentral_distance_km(frame.longitude.to_numpy(),frame.latitude.to_numpy(),anchor.longitude,anchor.latitude)
        mask=delta.ge(0).to_numpy()&delta.lt(days).to_numpy()&(distance<=radius_km)
        removed |= mask
        end=anchor.time+pd.Timedelta(days=days)
        anchors.append({'anchor_id':anchor.id,'anchor_time':anchor.time.isoformat(),'magnitude':anchor.mag,
            'events_in_window':int(mask.sum()),'fully_inside_study':None if study_bounds is None else bool(anchor.time>=study_bounds[0] and end<=study_bounds[1])})
    return removed,pd.DataFrame(anchors)


def reporting_profile(joined,config):
    records=[]
    regions=['All']+[r['name'] for r in config['regions']]+['Other']
    for region in regions:
        for year in range(config['start_year'],config['end_year']+1):
            part=joined.loc[joined.year.eq(year)&(True if region=='All' else joined.region.eq(region))]
            n=len(part)
            pct=lambda mask:float(mask.mean()*100) if n else np.nan
            result={'region':region,'year':year,'n':n,'mw_prefix_pct':pct(part.magType.fillna('').astype(str).str.lower().str.startswith('mw')),
                'automatic_pct':pct(part.status.fillna('').str.lower().eq('automatic')),
                'depth_10km_pct':pct(part.depth.eq(10)),'depth_33km_pct':pct(part.depth.eq(33)),
                'mag_5_to_5_2_pct':pct(part.mag.ge(5)&part.mag.lt(5.2)),
                'missing_magnitude_type_pct':pct(part.magType.isna()|part.magType.fillna('').str.strip().eq(''))}
            for col in QUALITY_FIELDS:result[col+'_available_pct']=pct(part[col].notna())
            records.append(result)
    return pd.DataFrame(records)


def category_mix(joined,column):
    part=joined.copy();part[column]=part[column].fillna('Missing').astype(str).str.strip().str.lower().replace('','missing')
    count=part.groupby(['year',column]).size().rename('count').reset_index()
    count['share_pct']=count['count']/count.groupby('year')['count'].transform('sum')*100
    return count


def slope_table(annual):
    records=[]
    for (region,threshold),group in annual.groupby(['region','threshold'],sort=False):
        group=group.sort_values('year');x=group.year.to_numpy();y=group['count'].to_numpy()
        slopes=[sen_slope(np.delete(x,i),np.delete(y,i)) for i in range(len(x))] if len(x)>2 else []
        records.append({'region':region,'threshold':threshold,'sen_slope_events_per_year':sen_slope(x,y),
            'leave_one_year_out_min':min(slopes) if slopes else None,'leave_one_year_out_max':max(slopes) if slopes else None,
            'maximum_year':int(x[np.argmax(y)]),'maximum_count':int(y.max()),'minimum_year':int(x[np.argmin(y)]),'minimum_count':int(y.min())})
    return pd.DataFrame(records)


def records(table):
    return json.loads(table.to_json(orient='records',double_precision=15))


def analyze_temporal(frame,raw,config,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    joined=join_reporting_metadata(frame,raw)
    periods=equal_periods(config['start_year'],config['end_year'])
    annual=annual_panel(frame,config);comparison=compare_periods(annual,periods)
    quality=reporting_profile(joined,config);slopes=slope_table(annual)
    mix=category_mix(joined,'magType');network=category_mix(joined,'net')
    tables={'annual_region_threshold':annual,'equal_period_comparison':comparison,'annual_reporting_profile':quality,
        'annual_magnitude_type_mix':mix,'annual_network_mix':network,'descriptive_slopes':slopes}
    # Full month grid diagnoses missing extraction partitions, not detection completeness.
    months=pd.period_range(f"{config['start_year']}-01",f"{config['end_year']}-12",freq='M')
    monthly=frame.groupby(frame.time.dt.tz_localize(None).dt.to_period('M')).size().reindex(months,fill_value=0)
    tables['monthly_coverage']=pd.DataFrame({'month':months.astype(str),'count':monthly.to_numpy()})
    bounds=(pd.Timestamp(f"{config['start_year']}-01-01",tz='UTC'),pd.Timestamp(f"{config['end_year']+1}-01-01",tz='UTC'))
    removed,anchors=sequence_window_mask(frame,study_bounds=bounds)
    tables['sequence_windows']=anchors
    filtered=annual_panel(frame.loc[~removed],config)
    tables['window_removal_annual']=filtered
    sensitivity=[]
    for name,mask in [('All preferred types',np.ones(len(frame),dtype=bool)),
        ('mw-prefix types',frame.magType.fillna('').str.lower().str.startswith('mw').to_numpy()),
        ('Reviewed only',frame.status.fillna('').str.lower().eq('reviewed').to_numpy()),
        ('Outside M8+ windows',~removed)]:
        result=compare_periods(annual_panel(frame.loc[mask],config),periods)
        result.insert(0,'selection',name);sensitivity.append(result)
    tables['selection_sensitivity']=pd.concat(sensitivity,ignore_index=True)
    box_results=[]
    for degrees in [-2,0,2]:
        boxes=json.loads(json.dumps(config['regions']))
        for box in boxes:
            box['lon']=[(box['lon'][0]-degrees+180)%360-180,(box['lon'][1]+degrees+180)%360-180]
            box['lat']=[max(-90,box['lat'][0]-degrees),min(90,box['lat'][1]+degrees)]
        candidate=frame.copy();candidate['region']=assign_regions(candidate.longitude.to_numpy(),candidate.latitude.to_numpy(),boxes)
        result=compare_periods(annual_panel(candidate,config),periods);result.insert(0,'expansion_degrees',degrees);box_results.append(result)
    tables['region_box_period_sensitivity']=pd.concat(box_results,ignore_index=True)
    # Five-year blocks, final block extends to 2025 (six years); annual means correct for length.
    blocks=[(year,min(year+4,config['end_year'])) for year in range(config['start_year'],config['end_year']+1,5)]
    if len(blocks)>1 and blocks[-1][1]-blocks[-1][0]+1<3:
        blocks[-2]=(blocks[-2][0],blocks[-1][1]);blocks.pop()
    block_rows=[]
    for (region,threshold),group in annual.groupby(['region','threshold'],sort=False):
        for start,end in blocks:
            part=group.loc[group.year.between(start,end)];n=int(part['count'].sum());days=int(part.exposure_days.sum())
            block_rows.append({'region':region,'threshold':threshold,'period':f'{start}–{end}','calendar_years':end-start+1,
                'count':n,'exposure_days':days,'annual_mean':n/(end-start+1),'rate_per_365_2425_days':n*365.2425/days})
    tables['multiyear_blocks']=pd.DataFrame(block_rows)
    period_quality=[]
    for start,end in periods:
        part=joined.loc[joined.year.between(start,end)]
        period_quality.append({'period':f'{start}–{end}','n':len(part),
            'mw_prefix_pct':float(part.magType.fillna('').str.lower().str.startswith('mw').mean()*100),
            'depth_10km_pct':float(part.depth.eq(10).mean()*100),'depth_33km_pct':float(part.depth.eq(33).mean()*100),
            'automatic_pct':float(part.status.fillna('').str.lower().eq('automatic').mean()*100),
            **{col+'_available_pct':float(part[col].notna().mean()*100) for col in QUALITY_FIELDS}})
    tables['period_reporting_comparison']=pd.DataFrame(period_quality)
    for name,value in tables.items():value.to_csv(output/(name+'.csv'),index=False,lineterminator='\n')
    summary={'version':VERSION,'n_events':len(frame),'periods':periods,'thresholds':list(THRESHOLDS),
        'global_period_comparisons':records(comparison.loc[comparison.region.eq('All')]),
        'regional_m5_comparison':records(comparison.loc[comparison.region.ne('All')&comparison.threshold.eq(5)]),
        'global_slopes':records(slopes.loc[slopes.region.eq('All')]),'period_reporting':period_quality,
        'sequence_sensitivity':{'anchors':len(anchors),'removed_unique_events':int(removed.sum()),'kept_events':int((~removed).sum()),
            'incomplete_anchor_windows':int((~anchors.fully_inside_study).sum()) if len(anchors) else 0},
        'missing_calendar_months':int(monthly.eq(0).sum()),
        'comparability_conclusion':'Recorded catalogue comparisons are supported under matched windows and definitions; uniform detection completeness and homogeneous magnitude/depth measurement are not established.'}
    write_json(output/'summary.json',summary)
    return tables,summary
