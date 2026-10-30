import importlib
import numpy as np
import pandas as pd
import pytest


def test_survival_counts_are_exact_at_observed_magnitude_cutpoints():
    module = importlib.import_module('earthquake_explorer.analysis')
    out = module.magnitude_frequency(pd.Series([5.,5.1,5.1,6.]))
    assert out.magnitude.tolist() == [5.,5.1,6.]
    assert out.cumulative_count.tolist() == [4,3,1]


def test_case_windows_wrap_date_line_exclude_anchor_and_use_equal_exposure():
    module = importlib.import_module('earthquake_explorer.analysis')
    times = ['2011-03-11T01:00Z','2011-03-10T01:00Z','2011-03-12T01:00Z',
             '2011-04-10T01:00Z','2011-03-12T01:00Z']
    frame = pd.DataFrame({'id':['anchor','before','after','right_edge','far'],
        'time':pd.to_datetime(times,utc=True), 'latitude':[0]*5,
        'longitude':[179,-179,-179,179,0], 'mag':[9.,5.,5.,5.,5.]})
    anchor = frame.iloc[0]
    sample,stats = module.case_sample(frame,anchor,30,500,2000,2025)
    assert set(sample.id) == {'before','after'}
    assert stats['before_count'] == stats['after_count'] == 1
    assert stats['fully_observed'] is True


def test_incomplete_case_windows_are_flagged():
    module = importlib.import_module('earthquake_explorer.analysis')
    frame = pd.DataFrame({'id':['a'],'time':pd.to_datetime(['2000-01-02'],utc=True),
        'latitude':[0], 'longitude':[0], 'mag':[9.]})
    _,stats = module.case_sample(frame,frame.iloc[0],30,500,2000,2025)
    assert stats['fully_observed'] is False


def test_spearman_drops_missing_pairwise_and_handles_constant_input():
    module = importlib.import_module('earthquake_explorer.analysis')
    assert module.correlation_pair(pd.Series([1,2,3,np.nan]),pd.Series([3,2,1,0])) == {'n':3,'rho':-1.0}
    assert module.correlation_pair(pd.Series([1,1,1]),pd.Series([1,2,3])) == {'n':3,'rho':None}
