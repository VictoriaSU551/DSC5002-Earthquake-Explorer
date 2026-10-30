"""Deterministic, exclusion-audited cleaning and geographic comparison boxes."""
import numpy as np
import pandas as pd


def assign_regions(longitude, latitude, regions):
    names = np.full(len(longitude), 'Other', dtype=object)
    for region in regions:
        lo, hi = region['lon']
        # Half-open longitude, closed latitude; priority is config order.
        inside_lon = ((longitude >= lo) & (longitude < hi)) if lo < hi else ((longitude >= lo) | (longitude < hi))
        mask = inside_lon & (latitude >= region['lat'][0]) & (latitude <= region['lat'][1]) & (names == 'Other')
        names[mask] = region['name']
    return names


def classify_depth(depth, cutpoints=(70, 300)):
    return np.select([depth.isna(), depth < cutpoints[0], depth < cutpoints[1]],
                     ['Missing','Shallow','Intermediate'], default='Deep')


def clean_events(frame, config):
    frame = frame.copy()
    required = ['id','time','latitude','longitude','depth','mag']
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    audit = {'input_rows':len(frame), 'steps':[], 'raw_missing':{c:int(frame[c].isna().sum()) for c in required}}
    for column in ['latitude','longitude','depth','mag']:
        frame[column] = pd.to_numeric(frame[column], errors='coerce').replace([np.inf,-np.inf],np.nan)
    frame['time'] = pd.to_datetime(frame['time'], utc=True, errors='coerce', format='mixed')
    def retain(mask, reason):
        nonlocal frame
        previous = len(frame)
        frame = frame.loc[mask].copy()
        audit['steps'].append({'reason':reason, 'removed':previous-len(frame), 'remaining':len(frame)})
    retain(frame.id.notna() & frame.id.astype(str).str.strip().ne(''), 'missing event ID')
    # USGS preferred entries are normally unique; if repeated, prefer latest update.
    if 'updated' in frame:
        frame['updated'] = pd.to_datetime(frame.updated,utc=True,errors='coerce',format='mixed')
        frame = frame.sort_values('updated',kind='stable',na_position='first')
    retain(~frame.id.duplicated(keep='last'), 'duplicate event ID')
    lower = pd.Timestamp(f"{config['start_year']}-01-01",tz='UTC')
    upper = pd.Timestamp(f"{config['end_year']+1}-01-01",tz='UTC')
    retain(frame.time.ge(lower) & frame.time.lt(upper), 'invalid time or outside half-open study period')
    retain(frame.latitude.between(-90,90) & frame.longitude.between(-180,180), 'missing or invalid coordinates')
    retain(frame.mag.ge(config['min_magnitude']), 'missing magnitude or below threshold')
    if 'type' in frame:
        retain(frame.type.eq('earthquake'), 'non-earthquake event type')
    frame['year'] = frame.time.dt.year
    frame['region'] = assign_regions(frame.longitude.to_numpy(),frame.latitude.to_numpy(),config['regions'])
    frame['depth_class'] = classify_depth(frame.depth,config.get('depth_thresholds_km',[70,300]))
    frame['negative_depth'] = frame.depth.lt(0)
    frame['magnitude_band'] = pd.cut(frame.mag,[5,6,7,8,np.inf],right=False,labels=['5–<6','6–<7','7–<8','8+']).astype(str)
    keep = required + [c for c in ['magType','place','status','updated','type'] if c in frame]
    keep += ['year','region','depth_class','negative_depth','magnitude_band']
    frame = frame[keep].sort_values(['time','id'],kind='stable').reset_index(drop=True)
    audit.update(retained_rows=len(frame),missing_depth=int(frame.depth.isna().sum()),
                 negative_depth_retained=int(frame.negative_depth.sum()),
                 suspicious_depth_above_800_km=int(frame.depth.gt(800).sum()))
    return frame,audit
