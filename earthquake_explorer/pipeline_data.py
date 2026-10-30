"""Preparation with input/code/output hash binding for safe cache reuse."""
from pathlib import Path
import json
import pandas as pd
from .io_utils import sha256, write_json
from .prepare import clean_events
from .geometry import nearest_boundary_km


def prepare_data(root,config):
    root = Path(root)
    lock = root/'data/sources.lock.json'
    if not lock.exists():
        raise FileNotFoundError('Download sources first: python run_pipeline.py')
    manifest = json.loads(lock.read_text(encoding='utf-8'))
    for record in manifest['files']:
        path = root/record['file']
        if not path.is_file() or sha256(path)!=record['sha256']:
            raise ValueError(f"Missing or modified source: {record['file']}")
    binding = {'source_lock_sha256':sha256(lock),'config_sha256':sha256(root/'config.json'),
               'code_sha256':{name:sha256(Path(__file__).with_name(name)) for name in ['pipeline_data.py','prepare.py','geometry.py']}}
    processed = root/'data/processed/earthquakes.csv'
    seal = root/'data/processed/processing_manifest.json'
    if processed.exists() and seal.exists():
        previous = json.loads(seal.read_text(encoding='utf-8'))
        if previous['binding']==binding and previous['dataset_sha256']==sha256(processed):
            print('Reusing verified cleaned dataset and distances.',flush=True)
            result = pd.read_csv(processed,float_precision='round_trip')
            result['time'] = pd.to_datetime(result.time,utc=True,format='mixed')
            return result,json.loads((processed.parent/'cleaning_audit.json').read_text(encoding='utf-8'))
    batches = [pd.read_csv(root/f'data/raw/usgs/{year}.csv') for year in range(config['start_year'],config['end_year']+1)]
    if any(len(batch)>=20000 for batch in batches):
        raise ValueError('An annual batch reached the API limit; subdivide the query before proceeding.')
    raw = pd.concat(batches,ignore_index=True)
    timestamps = pd.to_datetime(raw.time,utc=True,format='mixed')
    in_study = timestamps.ge(pd.Timestamp(f"{config['start_year']}-01-01",tz='UTC')) & timestamps.lt(pd.Timestamp(f"{config['end_year']+1}-01-01",tz='UTC'))
    source_count = raw.loc[in_study,'id'].nunique()
    if source_count != manifest['source_count']:
        raise ValueError(f"Source count mismatch: batches {source_count}, count receipt {manifest['source_count']}. Investigate catalogue revisions.")
    result,audit = clean_events(raw,config)
    audit['source_unique_in_period'] = source_count
    boundaries = json.loads((root/'data/raw/geography/PB2002_boundaries.json').read_text(encoding='utf-8'))
    print(f'Computing exact spherical boundary distances for {len(result):,} events...',flush=True)
    result['boundary_distance_km'] = nearest_boundary_km(result.longitude.to_numpy(),result.latitude.to_numpy(),boundaries)
    processed.parent.mkdir(parents=True,exist_ok=True)
    # Keep full floating-point precision so a first run and a cached run
    # yield the same threshold counts even for high-precision magnitudes.
    result.to_csv(processed,index=False)
    write_json(processed.parent/'cleaning_audit.json',audit)
    write_json(seal,{'binding':binding,'dataset_sha256':sha256(processed),'rows':len(result)})
    print('Cleaned dataset and boundary distances saved.',flush=True)
    return result,audit
