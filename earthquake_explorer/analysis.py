"""Descriptive tables for the five research questions; no predictive claims."""
from itertools import combinations
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from .geometry import epicentral_distance_km
from .prepare import classify_depth, assign_regions
from .io_utils import write_json

DEPTH_ORDER = ['Shallow','Intermediate','Deep','Missing']


def numeric_summary(series):
    values = series.dropna()
    if len(values) == 0:
        return {'n':0,'missing_pct':100.0,'mean':None,'median':None,'std':None,'q05':None,'q25':None,'q75':None,'q95':None,'iqr':None}
    q = values.quantile([.05,.25,.75,.95])
    return {'n':int(len(values)), 'missing_pct':float(series.isna().mean()*100),
            'mean':float(values.mean()),'median':float(values.median()),
            'std':float(values.std()) if len(values)>1 else None,
            'q05':float(q.loc[.05]),'q25':float(q.loc[.25]),'q75':float(q.loc[.75]),
            'q95':float(q.loc[.95]),'iqr':float(q.loc[.75]-q.loc[.25])}


def magnitude_frequency(magnitudes):
    counts = magnitudes.value_counts().sort_index(ascending=False).cumsum().sort_index()
    return pd.DataFrame({'magnitude':counts.index.to_numpy(),'cumulative_count':counts.to_numpy()})


def correlation_pair(x,y):
    pair = pd.concat([x,y],axis=1).dropna()
    rho = None
    if len(pair)>2 and pair.iloc[:,0].nunique()>1 and pair.iloc[:,1].nunique()>1:
        rho = float(spearmanr(pair.iloc[:,0],pair.iloc[:,1]).statistic)
    return {'n':len(pair),'rho':rho}


def select_anchor(frame,case):
    day = pd.Timestamp(case['date'],tz='UTC')
    candidates = frame.loc[frame.time.ge(day)&frame.time.lt(day+pd.Timedelta(days=1))]
    if candidates.empty:
        raise ValueError(f"No anchor event on {case['date']}")
    return candidates.sort_values(['mag','time','id'],ascending=[False,True,True]).iloc[0]


def case_sample(frame,anchor,days,radius_km,start_year,end_year):
    delta = (frame.time-anchor.time).dt.total_seconds()/86400
    spatial = epicentral_distance_km(frame.longitude.to_numpy(),frame.latitude.to_numpy(),anchor.longitude,anchor.latitude)
    mask = delta.ge(-days)&delta.lt(days)&(spatial<=radius_km)&frame.id.ne(anchor.id)
    selected = frame.loc[mask].copy()
    selected['relative_days'] = delta[mask]
    selected['anchor_distance_km'] = spatial[mask.to_numpy()]
    complete = (anchor.time-pd.Timedelta(days=days)>=pd.Timestamp(f'{start_year}-01-01',tz='UTC')
                and anchor.time+pd.Timedelta(days=days)<=pd.Timestamp(f'{end_year+1}-01-01',tz='UTC'))
    before = int(selected.relative_days.lt(0).sum())
    after = int(selected.relative_days.ge(0).sum())
    return selected,{'anchor_id':anchor.id,'anchor_time':anchor.time.isoformat(),'anchor_magnitude':float(anchor.mag),
                     'anchor_longitude':float(anchor.longitude),'anchor_latitude':float(anchor.latitude),
                     'days_each_side':days,'radius_km':radius_km,'before_count':before,'after_count':after,
                     'fully_observed':bool(complete),'before_per_day':before/days,'after_per_day':after/days}


def analyze(frame, config, output):
    output.mkdir(parents=True,exist_ok=True)
    regions = [r['name'] for r in config['regions']]+['Other']
    years = list(range(config['start_year'],config['end_year']+1))
    annual = frame.groupby('year').size().reindex(years,fill_value=0).rename('count')
    annual.to_csv(output/'annual_counts.csv')
    region_year = pd.crosstab(frame.region,frame.year).reindex(index=regions,columns=years,fill_value=0)
    region_year.to_csv(output/'region_year_counts.csv')
    depth_counts = pd.crosstab(frame.region,frame.depth_class).reindex(index=regions,columns=DEPTH_ORDER,fill_value=0)
    depth_counts.to_csv(output/'region_depth_counts.csv')
    frame.groupby('magnitude_band').size().rename('count').to_csv(output/'magnitude_band_counts.csv')
    magnitude_frequency(frame.mag).to_csv(output/'magnitude_frequency.csv',index=False)
    numeric = {c:numeric_summary(frame[c]) for c in ['mag','depth','boundary_distance_km']}
    pd.DataFrame(numeric).T.to_csv(output/'numeric_summary.csv')
    region_stats = []
    for name in regions:
        part = frame.loc[frame.region.eq(name)]
        known = part.depth.notna().sum()
        region_stats.append({'region':name,'count':len(part),
            'median_depth_km':float(part.depth.median()) if known else None,
            'deep_pct_known_depth':float(part.depth.ge(300).sum()/known*100) if known else None,
            'median_boundary_distance_km':float(part.boundary_distance_km.median()) if len(part) else None,
            'within_100km_pct':float(part.boundary_distance_km.le(100).mean()*100) if len(part) else None})
    pd.DataFrame(region_stats).to_csv(output/'regional_summary.csv',index=False)
    correlations = []
    for name,part in [('All',frame)]+[(r,frame.loc[frame.region.eq(r)]) for r in regions]+[
        ('2000–2012',frame.loc[frame.year.le(2012)]),('2013–2025',frame.loc[frame.year.ge(2013)])]:
        for x,y in combinations(['mag','depth','boundary_distance_km'],2):
            correlations.append({'group':name,'x':x,'y':y,**correlation_pair(part[x],part[y])})
    pd.DataFrame(correlations).to_csv(output/'spearman_correlations.csv',index=False)
    cases, sensitivity = [],[]
    for case in config['cases']:
        anchor = select_anchor(frame,case)
        sample,stats = case_sample(frame,anchor,config['case_window_days'],config['case_radius_km'],config['start_year'],config['end_year'])
        cases.append({'name':case['name'],**stats})
        slug = case['date']
        sample.to_csv(output/f'case_{slug}_events.csv',index=False)
        for days in [7,30,90]:
            for radius in [250,500,1000]:
                _,result = case_sample(frame,anchor,days,radius,config['start_year'],config['end_year'])
                sensitivity.append({'name':case['name'],**result})
    pd.DataFrame(cases).to_csv(output/'case_summary.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(output/'case_window_sensitivity.csv',index=False)
    depth_sensitivity = []
    for cuts in [(60,300),(70,300),(70,350)]:
        counts = pd.Series(classify_depth(frame.depth,cuts)).value_counts()
        depth_sensitivity.append({'shallow_cutoff':cuts[0],'deep_cutoff':cuts[1],
                                  **{c:int(counts.get(c,0)) for c in DEPTH_ORDER}})
    pd.DataFrame(depth_sensitivity).to_csv(output/'depth_threshold_sensitivity.csv',index=False)
    region_sensitivity = []
    for expansion in [-2,0,2]:
        boxes = json.loads(json.dumps(config['regions']))
        for box in boxes:
            box['lat'] = [max(-90,box['lat'][0]-expansion),min(90,box['lat'][1]+expansion)]
            box['lon'] = [((box['lon'][0]-expansion+180)%360)-180,((box['lon'][1]+expansion+180)%360)-180]
        names = assign_regions(frame.longitude.to_numpy(),frame.latitude.to_numpy(),boxes)
        for name in regions:
            region_sensitivity.append({'box_expansion_degrees':expansion,'region':name,'count':int((names==name).sum())})
    pd.DataFrame(region_sensitivity).to_csv(output/'region_box_sensitivity.csv',index=False)
    summary = {'n_events':len(frame),'period_utc':[frame.time.min().isoformat(),frame.time.max().isoformat()],
        'annual_max':{'year':int(annual.idxmax()),'count':int(annual.max())},
        'annual_min':{'year':int(annual.idxmin()),'count':int(annual.min())},
        'numeric':numeric, 'within_boundary_km_pct':{str(k):float(frame.boundary_distance_km.le(k).mean()*100) for k in [50,100,250]},
        'depth_counts':{k:int(frame.depth_class.eq(k).sum()) for k in DEPTH_ORDER},
        'magnitude_at_least_7':int(frame.mag.ge(7).sum()),'magnitude_at_least_8':int(frame.mag.ge(8).sum()),
        'regions':region_stats,'correlations_all':[r for r in correlations if r['group']=='All'],'cases':cases}
    write_json(output/'summary.json',summary)
    return summary
