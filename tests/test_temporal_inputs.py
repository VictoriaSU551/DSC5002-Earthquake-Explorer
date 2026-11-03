import hashlib
import importlib
import json
from pathlib import Path
import pytest


def setup_snapshot(root):
    def put(relative,text):
        p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');return p
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    config=put('config.json','{"start_year":2025,"end_year":2025,"min_magnitude":5,"regions":[]}')
    raw=put('data/raw/usgs/2025.csv','id,time,latitude,longitude,depth,mag\na,2025-01-01T00:00:00Z,0,0,10,5.0876669931811\n')
    source=put('data/sources.lock.json',json.dumps({'files':[{'file':'data/raw/usgs/2025.csv','sha256':digest(raw)}]}))
    data=put('data/processed/earthquakes.csv',raw.read_text(encoding='utf-8'))
    code=put('earthquake_explorer/prepare.py','# frozen code\n')
    put('data/processed/processing_manifest.json',json.dumps({'rows':1,'dataset_sha256':digest(data),'binding':{
        'source_lock_sha256':digest(source),'config_sha256':digest(config),'code_sha256':{'prepare.py':digest(code)}}}))
    return config,raw,data


def test_read_only_loader_keeps_full_precision(tmp_path):
    setup_snapshot(tmp_path)
    m=importlib.import_module('earthquake_explorer.temporal_inputs')
    assert m.load_verified_snapshot(tmp_path).mag.tolist()==[5.0876669931811]


@pytest.mark.parametrize('changed',['config.json','data/raw/usgs/2025.csv','earthquake_explorer/prepare.py'])
def test_changed_snapshot_binding_fails_without_writing_dataset_or_seal(tmp_path,changed):
    setup_snapshot(tmp_path)
    m=importlib.import_module('earthquake_explorer.temporal_inputs')
    path=tmp_path/changed;path.write_bytes(path.read_bytes()+b'\n')
    watched=[tmp_path/'data/processed/earthquakes.csv',tmp_path/'data/processed/processing_manifest.json']
    before=[(p.read_bytes(),p.stat().st_mtime_ns) for p in watched]
    with pytest.raises(ValueError):m.load_verified_snapshot(tmp_path)
    assert before==[(p.read_bytes(),p.stat().st_mtime_ns) for p in watched]


def test_missing_seal_fails_without_rebuilding(tmp_path):
    _,_,data=setup_snapshot(tmp_path)
    m=importlib.import_module('earthquake_explorer.temporal_inputs')
    (tmp_path/'data/processed/processing_manifest.json').unlink()
    before=(data.read_bytes(),data.stat().st_mtime_ns)
    with pytest.raises(ValueError):m.load_verified_snapshot(tmp_path)
    assert before==(data.read_bytes(),data.stat().st_mtime_ns)
