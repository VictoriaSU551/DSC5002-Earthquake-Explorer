import importlib
import pandas as pd
import pytest


def test_cleaning_retains_negative_and_missing_depth_but_rejects_invalid_events():
    module = importlib.import_module('earthquake_explorer.prepare')
    rows = [
        ['a', '2000-01-01T00:00:00Z', 0, 180, -1, 5],
        ['a', '2000-01-01T00:00:00Z', 0, 180, -1, 5],
        ['b', '2025-12-31T23:59:59.999Z', 10, -180, None, 6],
        ['c', '2026-01-01T00:00:00Z', 0, 0, 10, 7],
        ['d', '2001-01-01T00:00:00Z', 91, 0, 10, 6],
        ['e', '2001-01-01T00:00:00Z', 0, 0, 10, 4.9],
    ]
    frame = pd.DataFrame(rows, columns=['id', 'time', 'latitude', 'longitude', 'depth', 'mag'])
    frame['type'] = 'earthquake'
    clean, audit = module.clean_events(frame, {'start_year':2000,'end_year':2025,'min_magnitude':5,'regions':[]})
    assert clean.id.tolist() == ['a', 'b']
    assert clean.loc[0, 'negative_depth']
    assert clean.loc[1, 'depth_class'] == 'Missing'
    assert audit['input_rows'] == 6
    assert audit['retained_rows'] == 2
    assert sum(x['removed'] for x in audit['steps']) == 4


def test_regions_have_date_line_support_and_depth_cutpoints():
    module = importlib.import_module('earthquake_explorer.prepare')
    frame = pd.DataFrame({'id':['a','b','c','d'], 'time':['2011-01-01']*4,
        'latitude':[-20]*4, 'longitude':[179,-179,0,170], 'depth':[69.99,70,300,None], 'mag':[5]*4})
    clean, _ = module.clean_events(frame, {'start_year':2000,'end_year':2025,'min_magnitude':5,
        'regions':[{'name':'Dateline','lon':[165,-170],'lat':[-40,-10]}]})
    assert clean.region.tolist() == ['Dateline','Dateline','Other','Dateline']
    assert clean.depth_class.tolist() == ['Shallow','Intermediate','Deep','Missing']
