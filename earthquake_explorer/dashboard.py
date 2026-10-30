"""Assemble a standalone HTML dashboard: no CDN, map tiles or Python server."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from matplotlib.path import Path as PolygonPath
from plotly.offline import get_plotlyjs
from .geometry import geometry_lines
from .analysis import select_anchor, case_sample


def safe_json(value):
    # USGS text belongs in JSON/text nodes, never raw executable HTML.
    return json.dumps(value,separators=(',',':'),ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')


def build_dashboard(frame,config,root):
    geography=root/'data/raw/geography'
    boundaries=json.loads((geography/'PB2002_boundaries.json').read_text(encoding='utf-8'))
    coast=json.loads((geography/'ne_110m_coastline.geojson').read_text(encoding='utf-8'))
    land=json.loads((geography/'ne_110m_land.geojson').read_text(encoding='utf-8'))
    regions=[r['name'] for r in config['regions']]+['Other']
    depth_names=['Shallow','Intermediate','Deep','Missing']
    rows=[]
    for row in frame.itertuples():
        rows.append([row.id,row.time.isoformat(),round(row.latitude,5),round(row.longitude,5),
                     None if pd.isna(row.depth) else round(row.depth,3),float(row.mag),round(row.boundary_distance_km,5),
                     regions.index(row.region),depth_names.index(row.depth_class),str(getattr(row,'place',''))])
    cases=[]
    for case in config['cases']:
        anchor=select_anchor(frame,case)
        sample,stats=case_sample(frame,anchor,config['case_window_days'],config['case_radius_km'],config['start_year'],config['end_year'])
        cases.append({'name':case['name'],**stats,'indices':frame.index[frame.id.isin(sample.id)].tolist(),
                      'relative_days':sample.relative_days.tolist()})
    # Low-resolution globe land mask from the actual Natural Earth land polygons.
    lons,lats=np.meshgrid(np.linspace(-180,180,121),np.linspace(-90,90,61))
    grid=np.column_stack([lons.ravel(),lats.ravel()])
    mask=np.zeros(len(grid),dtype=bool)
    for feature in land['features']:
        polygons=[feature['geometry']['coordinates']] if feature['geometry']['type']=='Polygon' else feature['geometry']['coordinates']
        for polygon in polygons:
            covered=PolygonPath(polygon[0]).contains_points(grid)
            for hole in polygon[1:]:covered &= ~PolygonPath(hole).contains_points(grid)
            mask |= covered
    payload={'rows':rows,'regions':regions,'depth_names':depth_names,'config':config,
             'boundaries':[x.round(5).tolist() for x in geometry_lines(boundaries)],
             'coast':[x.round(5).tolist() for x in geometry_lines(coast)],
             'land':[x.round(5).tolist() for x in geometry_lines(land)],
             'globe_land':mask.reshape(lons.shape).astype(int).tolist(),'cases':cases}
    template=(root/'web/dashboard.html').read_text(encoding='utf-8')
    html=template.replace('/*__PLOTLY__*/',get_plotlyjs())
    html=html.replace('/*__CSS__*/',(root/'web/style.css').read_text(encoding='utf-8'))
    html=html.replace('/*__DATA__*/',safe_json(payload))
    html=html.replace('/*__APP__*/',(root/'web/dashboard.js').read_text(encoding='utf-8'))
    target=root/'outputs/dashboard.html'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(html,encoding='utf-8')
    return target
