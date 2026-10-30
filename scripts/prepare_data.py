from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from earthquake_explorer.pipeline_data import prepare_data
from earthquake_explorer.analysis import analyze

if __name__=='__main__':
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    frame,audit=prepare_data(ROOT,config)
    summary=analyze(frame,config,ROOT/'outputs/tables')
    print(json.dumps({'audit':audit,'summary':summary},indent=2))
