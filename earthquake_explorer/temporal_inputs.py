"""Read a verified baseline snapshot without any preparation/rebuild fallback."""
import json
from pathlib import Path
import pandas as pd
from .io_utils import sha256


def load_verified_snapshot(root):
    root=Path(root)
    try:
        seal=json.loads((root/'data/processed/processing_manifest.json').read_text(encoding='utf-8'))
        source=json.loads((root/'data/sources.lock.json').read_text(encoding='utf-8'))
        binding=seal['binding']
        if sha256(root/'config.json')!=binding['config_sha256']:
            raise ValueError('Configuration differs from the frozen baseline binding')
        if sha256(root/'data/sources.lock.json')!=binding['source_lock_sha256']:
            raise ValueError('Source manifest differs from the frozen baseline binding')
        for name,digest in binding['code_sha256'].items():
            if sha256(root/'earthquake_explorer'/name)!=digest:
                raise ValueError(f'Baseline preparation code differs from its binding: {name}')
        for item in source['files']:
            if sha256(root/item['file'])!=item['sha256']:
                raise ValueError(f"Source hash mismatch: {item['file']}")
        if 'count_receipt' in source:
            if sha256(root/'data/raw/catalog_count.txt')!=source['count_receipt']['sha256']:
                raise ValueError('Count receipt hash mismatch')
        path=root/'data/processed/earthquakes.csv'
        if sha256(path)!=seal['dataset_sha256']:
            raise ValueError('Processed dataset differs from its frozen hash')
        frame=pd.read_csv(path,float_precision='round_trip')
        if len(frame)!=seal['rows'] or not frame.id.is_unique:
            raise ValueError('Frozen dataset row count or event ID grain is invalid')
        frame['time']=pd.to_datetime(frame.time,utc=True,format='mixed')
        return frame
    except (OSError,KeyError,json.JSONDecodeError) as error:
        raise ValueError('A complete, verified baseline snapshot is required; no input was rebuilt or changed.') from error
