"""Rebuild the integrated deliverables from the sealed, read-only catalogue."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.dashboard import build_dashboard
from earthquake_explorer.analysis import select_anchor,case_sample,analyze
from earthquake_explorer.sections import build_sections
from earthquake_explorer.magnitude_analysis import run as magnitude_run
from earthquake_explorer.io_utils import sha256

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/final'

def build():
    frame=load_verified_snapshot(ROOT)
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    baseline=json.loads((ROOT/'outputs/artifact_manifest.json').read_text(encoding='utf-8'))
    for record in baseline['files']:
        assert sha256(ROOT/record['path'])==record['sha256'],record['path']
    OUT.mkdir(exist_ok=True)
    summary=analyze(frame,config,OUT/'tables')
    build_dashboard(frame,config,ROOT,OUT/'dashboard.html')
    rq4=OUT/'rq4';(rq4/'data').mkdir(parents=True,exist_ok=True)
    magnitude_run(ROOT/'data',rq4)
    boundaries=json.loads((ROOT/'data/raw/geography/PB2002_boundaries.json').read_text(encoding='utf-8'))
    sections=build_sections(frame,boundaries)
    (OUT/'sections.json').write_text(json.dumps(sections),encoding='utf-8')
    cases=[]
    for case in config['cases']:
        anchor=select_anchor(frame,case)
        sample,stats=case_sample(frame,anchor,30,500,2000,2025)
        after=sample[sample.relative_days.ge(0)]
        counts=np.histogram(after.relative_days,bins=np.arange(31))[0]
        cases.append(dict(name=case['name'],**stats,peak_after_day=int(counts.argmax()),
             peak_day_count=int(counts.max()),first3_days_share_pct=float(after.relative_days.lt(3).mean()*100),
             largest_post_window_magnitude=float(after.mag.max())))
    pd.DataFrame(cases).to_csv(OUT/'tables/case_comparison.csv',index=False)
    summary['case_comparison']=cases
    summary['within_200km_pct']=float(frame.boundary_distance_km.le(200).mean()*100)
    summary['magnitude_counts']={str(m):int(frame.mag.ge(m).sum()) for m in range(5,10)}
    summary['data_sha256']=sha256(ROOT/'data/processed/earthquakes.csv')
    (OUT/'poster_facts.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    for record in baseline['files']:assert sha256(ROOT/record['path'])==record['sha256']
    print('Integrated results built; all 30 original deliverables preserved.')

if __name__=='__main__':build()
