"""Bounded, resumable USGS requests and immutable geography references."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import json
import time
import requests
from .io_utils import sha256, write_json

USGS = 'https://earthquake.usgs.gov/fdsnws/event/1/'
PB_COMMIT = '339b0c56563c118307b1f4542703047f5f698fae'
NE_COMMIT = 'ca96624a56bd078437bca8184e78163e5039ad19'
ASSETS = {
    'PB2002_boundaries.json': f'https://raw.githubusercontent.com/fraxen/tectonicplates/{PB_COMMIT}/GeoJSON/PB2002_boundaries.json',
    'ne_110m_coastline.geojson': f'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson/ne_110m_coastline.geojson',
    'ne_110m_land.geojson': f'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson/ne_110m_land.geojson',
    'PB2002_LICENSE.md': f'https://raw.githubusercontent.com/fraxen/tectonicplates/{PB_COMMIT}/LICENSE.md',
}


def download(url, path):
    """Reuse only a byte-verified cached response to the identical URL."""
    path = Path(path)
    receipt = path.with_name(path.name + '.receipt.json')
    if path.exists() and receipt.exists():
        meta = json.loads(receipt.read_text(encoding='utf-8'))
        if meta['url'] == url and meta['sha256'] == sha256(path):
            return meta
        raise ValueError(f'Cached source fails provenance check: {path.name}')
    for attempt in range(4):
        try:
            response = requests.get(url, timeout=(15, 120), headers={'User-Agent':'DSC5002-Earthquake-Explorer/0.1'})
            response.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + '.part')
            temporary.write_bytes(response.content)
            temporary.replace(path)
            meta = {'file':path.name, 'url':url, 'accessed_utc':datetime.now(timezone.utc).isoformat(),
                    'bytes':path.stat().st_size, 'sha256':sha256(path)}
            write_json(receipt, meta)
            return meta
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def annual_url(year, config):
    # USGS endpoints are inclusive. Deduplication and the half-open study filter
    # below safely handle any event at precisely 1 January midnight.
    params = {'format':'csv', 'starttime':f'{year}-01-01T00:00:00',
              'endtime':f'{year+1}-01-01T00:00:00', 'minmagnitude':config['min_magnitude'],
              'eventtype':'earthquake', 'orderby':'time-asc', 'limit':20000}
    return requests.Request('GET', USGS+'query', params=params).prepare().url


def acquire(root, config):
    root = Path(root)
    raw = root / 'data/raw'
    jobs = [(annual_url(y, config), raw/'usgs'/f'{y}.csv')
            for y in range(config['start_year'], config['end_year']+1)]
    jobs += [(u, raw/'geography'/name) for name,u in ASSETS.items()]
    def fetch(job):
        meta = download(*job)
        print(f"Source ready: {job[1].name}", flush=True)
        return {**meta, 'file':job[1].relative_to(root).as_posix()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, jobs))
    count_params = {'starttime':f"{config['start_year']}-01-01T00:00:00",
                    'endtime':f"{config['end_year']}-12-31T23:59:59.999",
                    'minmagnitude':config['min_magnitude'], 'eventtype':'earthquake'}
    count_url = requests.Request('GET',USGS+'count',params=count_params).prepare().url
    count_meta = download(count_url,raw/'catalog_count.txt')
    expected = int((raw/'catalog_count.txt').read_text().strip())
    manifest = {'schema_version':1, 'query':count_params, 'source_count':expected,
                'count_receipt':count_meta, 'files':receipts,
                'geography_commits':{'fraxen/tectonicplates':PB_COMMIT,'nvkelso/natural-earth-vector':NE_COMMIT}}
    write_json(root/'data/sources.lock.json',manifest)
    return manifest
