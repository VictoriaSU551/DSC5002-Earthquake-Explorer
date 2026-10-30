"""Download all project sources without running the analysis."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from earthquake_explorer.acquire import acquire

if __name__ == '__main__':
    acquire(ROOT,json.loads((ROOT/'config.json').read_text(encoding='utf-8')))
