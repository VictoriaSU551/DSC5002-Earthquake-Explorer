"""Verify submitted numerical claims against the canonical project snapshot."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import numpy as np
import pandas as pd
from earthquake_explorer.temporal_inputs import load_verified_snapshot
from earthquake_explorer.io_utils import sha256

ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'local_sources/team_submissions'
out=ROOT/'outputs/final';out.mkdir(exist_ok=True)
d=load_verified_snapshot(ROOT)
checks={}
inventory=json.loads((archive/'submission_inventory.json').read_text(encoding='utf-8-sig'))
checks['all_98_submitted_files_preserved']=all(sha256(archive/x['source'])==x['sha256'] for x in inventory)
rq4=next(archive.rglob('member4_analysis.py')).parent
raw=pd.concat([pd.read_csv(p) for p in sorted((rq4/'data/raw_usgs').glob('*.csv'))])
non=raw[raw.type.ne('earthquake')]
q=raw[raw.type.eq('earthquake')].set_index('id').loc[d.id]
checks['raw_46523_split_46463_earthquakes_60_other']=len(raw)==46523 and len(non)==60 and len(q)==46463
checks['raw_earthquake_ids_match']=set(q.index)==set(d.id) and q.index.is_unique
for col in ['mag','depth','longitude','latitude']:
    checks['rq4_raw_matches_frozen_'+col]=np.array_equal(q[col].to_numpy(),d[col].to_numpy(),equal_nan=True)
checks['raw_times_match']=np.array_equal(pd.to_datetime(q.time,utc=True,format='mixed').to_numpy(),d.time.to_numpy())
submitted=pd.read_csv(rq4/'tables/cumulative_frequency.csv')
for row in submitted.itertuples():
    sub=d
    if row.sample=='Mw family':sub=sub[sub.magType.isin(['mw','mwb','mwc','mwr','mww','mwp'])]
    if row.sample=='mb':sub=sub[sub.magType.eq('mb')]
    if row.period=='2000–2012':sub=sub[sub.year.le(2012)]
    if row.period=='2013–2025':sub=sub[sub.year.ge(2013)]
    checks[f'rq4_curve_{row.Index}']=int(sub.mag.ge(row.threshold).sum())==row.n_ge
m3=pd.read_csv(archive/'Member3/member3_region_summary.csv')
for row in m3.itertuples():
    sub=d if row.region=='All groups' else d[d.region.eq(row.region)]
    checks['rq3_region_'+row.region]=len(sub)==row.known_depth_n and int(sub.depth.ge(300).sum())==row.deep_n
facts=json.loads((out/'poster_facts.json').read_text())
m5=pd.read_csv(archive/'5002-question5/tables/case_comparison.csv')
for a,b in zip(m5.itertuples(),facts['case_comparison']):
    checks['rq5_counts_'+a.name]=a.before_count==b['before_count'] and a.after_count==b['after_count']
    checks['rq5_first3_'+a.name]=abs(a.first3_days_share_pct-b['first3_days_share_pct'])<1e-9
    checks['rq5_peak_'+a.name]=a.peak_day_count==b['peak_day_count'] and a.peak_day_after==b['peak_after_day']
    checks['rq5_largest_'+a.name]=a.largest_aftershock==b['largest_post_window_magnitude']
non[['id','type','time','mag']].to_csv(out/'tables/excluded_non_earthquakes.csv',index=False)
receipt={'checks':len(checks),'passed':sum(checks.values()),'failures':[k for k,v in checks.items() if not v],
 'non_earthquake_types':non.type.value_counts().to_dict(),'archive_files':len(inventory),
 'interpretation':'Member 2 source omits eventtype filter. The supplied all-type snapshot reproduces its 46,523 count; its 60-event revision explanation is unsupported. Exact Member 2 downloaded files were not supplied.',
 'canonical_sha256':sha256(ROOT/'data/processed/earthquakes.csv')}
(out/'submission_audit.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2));assert not receipt['failures']
