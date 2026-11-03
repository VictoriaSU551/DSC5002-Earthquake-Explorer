"""Build the versioned year/region extension without rewriting baseline outputs."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import argparse
import json
from pathlib import Path
import shutil
import pandas as pd
from earthquake_explorer.io_utils import sha256
from earthquake_explorer.temporal_utils import write_json
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.temporal_analysis import VERSION,analyze_temporal
from earthquake_explorer.temporal_figures import make_temporal_figures
from earthquake_explorer.temporal_report import build_temporal_views

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',action='store_true',help='Also copy aggregate results to docs/temporal_regional_v2 for Git publication')
    args=parser.parse_args()
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    if (config['start_year'],config['end_year'],config['min_magnitude'])!=(2000,2025,5):
        raise ValueError('This report implements the supplied 2000–2025 M>=5 protocol; update its narrative before changing scope.')
    baseline_manifest=ROOT/'outputs/artifact_manifest.json'
    if not baseline_manifest.exists():raise FileNotFoundError('Build the baseline first: python run_pipeline.py')
    baseline=json.loads(baseline_manifest.read_text(encoding='utf-8'))
    before={f['path']:sha256(ROOT/f['path']) for f in baseline['files']}
    if any(before[f['path']]!=f['sha256'] for f in baseline['files']):raise ValueError('Baseline artifact hash mismatch')
    data_before=sha256(ROOT/'data/processed/earthquakes.csv')
    input_paths=['config.json','data/sources.lock.json','data/processed/earthquakes.csv',
        'data/processed/processing_manifest.json','data/processed/cleaning_audit.json','outputs/artifact_manifest.json']
    input_hashes={p:sha256(ROOT/p) for p in input_paths}
    frame=load_verified_snapshot(ROOT)
    source=json.loads((ROOT/'data/sources.lock.json').read_text(encoding='utf-8'))
    batches=[];coverage=[]
    for year in range(2000,2026):
        path=ROOT/f'data/raw/usgs/{year}.csv';batch=pd.read_csv(path);batches.append(batch)
        time=pd.to_datetime(batch.time,utc=True,format='mixed')
        coverage.append({'year':year,'source_rows':len(batch),'source_columns':len(batch.columns),
            'unique_ids_inside_calendar_year':batch.loc[time.dt.year.eq(year),'id'].nunique(),
            'retained_events':int(frame.year.eq(year).sum()),'source_sha256':sha256(path)})
    output=ROOT/'outputs'/VERSION;tables_dir=output/'tables'
    tables,summary=analyze_temporal(frame,pd.concat(batches,ignore_index=True),config,tables_dir)
    tables['source_batch_coverage']=pd.DataFrame(coverage);tables['source_batch_coverage'].to_csv(tables_dir/'source_batch_coverage.csv',index=False,lineterminator='\n')
    dates=sorted({f['accessed_utc'].split('T')[0] for f in source['files']})
    provenance={'analysis_date':'2026-11-03','dataset_sha256':data_before,'source_access_dates':', '.join(dates),
        'baseline_artifact_manifest_sha256':sha256(baseline_manifest),'baseline_files_checked':len(before),
        'source_lock_sha256':sha256(ROOT/'data/sources.lock.json'),'input_hashes':input_hashes,
        'raw_metadata_join':'one-to-one by latest-update preferred event ID'}
    write_json(output/'provenance.json',provenance)
    print('Rendering nine additional figures...',flush=True)
    figures=make_temporal_figures(tables,summary,config,output/'figures')
    views=build_temporal_views(tables,summary,config,provenance,ROOT,output)
    if any(sha256(ROOT/p)!=digest for p,digest in input_hashes.items()) or any(sha256(ROOT/p)!=digest for p,digest in before.items()):
        raise AssertionError('The extension modified a baseline input or output')
    files=sorted(tables_dir.glob('*'))+figures+views+[output/'provenance.json']
    artifact_manifest={'version':VERSION,'events':len(frame),'baseline_preserved':True,
        'files':[{'path':p.relative_to(output).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files]}
    write_json(output/'artifact_manifest.json',artifact_manifest)
    if args.publish:
        destination=ROOT/'docs/temporal_regional_v2'
        for path in files:
            # Anchor-level sequence details remain in local outputs.
            if path.name=='sequence_windows.csv':continue
            target=destination/path.relative_to(output);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        write_json(destination/'artifact_manifest.json',{**artifact_manifest,'aggregate_only':True,
            'files':[f for f in artifact_manifest['files'] if f['path']!='tables/sequence_windows.csv']})
        print(f'Aggregate publication prepared: {destination}',flush=True)
    print(f'Built {len(frame):,} events; {len(figures)} NEW figures. Baseline unchanged.\nOpen: {output/"report.html"}',flush=True)


if __name__=='__main__':main()
