"""Build the complete baseline; --offline never calls the network."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import argparse
from pathlib import Path
import json
from earthquake_explorer.acquire import acquire
from earthquake_explorer.pipeline_data import prepare_data
from earthquake_explorer.analysis import analyze
from earthquake_explorer.figures import make_figures
from earthquake_explorer.dashboard import build_dashboard
from earthquake_explorer.report import build_report
from earthquake_explorer.io_utils import write_json,sha256

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Use only the verified local source cache')
    args=parser.parse_args()
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    if not args.offline:acquire(ROOT,config)
    frame,audit=prepare_data(ROOT,config)
    print('Producing analysis tables...',flush=True)
    summary=analyze(frame,config,ROOT/'outputs/tables')
    print('Rendering twelve research figures...',flush=True)
    figures=make_figures(frame,config,ROOT)
    print('Building offline dashboard and report...',flush=True)
    dashboard=build_dashboard(frame,config,ROOT)
    report=build_report(summary,audit,config,ROOT)
    files=sorted((ROOT/'outputs').glob('tables/*'))+figures+[dashboard,report]
    write_json(ROOT/'outputs/artifact_manifest.json',{'rows':len(frame),'files':[
        {'path':p.relative_to(ROOT).as_posix(),'sha256':sha256(p),'bytes':p.stat().st_size} for p in files]})
    print(f'Built {len(frame):,} events, {len(figures)} figures, dashboard and report.',flush=True)
    print(f'Open: {dashboard}\nOpen: {report}',flush=True)


if __name__=='__main__':main()
