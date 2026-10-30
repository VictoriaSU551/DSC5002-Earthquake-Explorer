import json
import hashlib
from pathlib import Path
import pandas as pd
from earthquake_explorer.pipeline_data import prepare_data


def test_first_run_and_cached_run_preserve_source_numeric_precision(tmp_path):
    config={'start_year':2025,'end_year':2025,'min_magnitude':5,'regions':[]}
    (tmp_path/'config.json').write_text(json.dumps(config),encoding='utf-8')
    raw=tmp_path/'data/raw/usgs';raw.mkdir(parents=True)
    geo=tmp_path/'data/raw/geography';geo.mkdir(parents=True)
    magnitude=5.0876669931811
    pd.DataFrame({'id':['precise'],'time':['2025-01-01T00:00:00Z'],
        'latitude':[1.],'longitude':[5.],'depth':[10.],'mag':[magnitude],
        'type':['earthquake']}).to_csv(raw/'2025.csv',index=False)
    (geo/'PB2002_boundaries.json').write_text(json.dumps({'features':[{'geometry':{
        'type':'LineString','coordinates':[[0,0],[10,0]]}}]}),encoding='utf-8')
    files=[]
    for p in [raw/'2025.csv',geo/'PB2002_boundaries.json']:
        files.append({'file':p.relative_to(tmp_path).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (tmp_path/'data/sources.lock.json').write_text(json.dumps({'source_count':1,'files':files}),encoding='utf-8')
    first,_=prepare_data(tmp_path,config)
    cached,_=prepare_data(tmp_path,config)
    assert first.mag.tolist()==cached.mag.tolist()==[magnitude]
    assert first.boundary_distance_km.tolist()==cached.boundary_distance_km.tolist()
