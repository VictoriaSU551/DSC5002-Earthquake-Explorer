import importlib
import pandas as pd
import pytest


def module():
    return importlib.import_module('earthquake_explorer.temporal_analysis')


def fixture():
    frame=pd.DataFrame({'id':['a','b','c','d'],'year':[2012,2012,2013,2013],
        'region':['R','R','R','Other'],'mag':[5.,6.,5.,7.]})
    config={'start_year':2012,'end_year':2013,'min_magnitude':5,'regions':[{'name':'R'}]}
    return frame,config


def test_annual_grid_preserves_zero_cells_and_leap_year_exposure():
    frame,config=fixture()
    panel=module().annual_panel(frame,config,thresholds=(5,6))
    row=panel.query("region=='Other' and year==2012 and threshold==6").iloc[0]
    assert row['count']==0 and row.exposure_days==366
    assert panel.query("region=='All' and threshold==5")['count'].tolist()==[2,2]
    assert panel.query("region=='R' and threshold==6")['count'].tolist()==[1,0]
    assert len(panel)==12


def test_period_ratios_use_exact_exposure_and_mark_zero_baselines_undefined():
    frame,config=fixture()
    m=module();comparison=m.compare_periods(m.annual_panel(frame,config,(5,6)),m.equal_periods(2012,2013))
    allrow=comparison.query("region=='All' and threshold==5").iloc[0]
    assert allrow.rate_ratio==pytest.approx(366/365)
    assert allrow.early_count==allrow.late_count==2
    r=comparison.query("region=='Other' and threshold==6").iloc[0]
    assert pd.isna(r.rate_ratio) and r.early_count==0 and r.late_count==1


def test_reporting_join_uses_latest_id_without_changing_analysis_grain():
    frame,_=fixture()
    raw=pd.DataFrame({'id':['a','a','b','c','d'], 'updated':['2020-01-01','2021-01-01','2020-01-01','2020-01-01','2020-01-01'],
        'depthError':[99,1,2,None,4],'net':['old','new','us','us','us']})
    joined=module().join_reporting_metadata(frame,raw)
    assert len(joined)==4 and joined.id.is_unique
    assert joined.loc[joined.id.eq('a'),'depthError'].iloc[0]==1
    assert joined.loc[joined.id.eq('a'),'net'].iloc[0]=='new'
    with pytest.raises(ValueError):module().join_reporting_metadata(frame,raw.loc[raw.id.ne('d')])


def test_window_union_handles_dateline_overlap_and_right_endpoint():
    m=module()
    frame=pd.DataFrame({'id':['anchor1','anchor2','member','right','far'],
        'time':pd.to_datetime(['2010-01-01','2010-01-02','2010-01-03','2010-02-01','2010-01-03'],utc=True),
        'longitude':[179,179,-179,179,0], 'latitude':[0]*5,'mag':[8,8,5,5,5]})
    mask,anchors=m.sequence_window_mask(frame,days=30,radius_km=500)
    assert frame.loc[mask,'id'].tolist()==['anchor1','anchor2','member']
    assert len(anchors)==2 and int(mask.sum())==3


def test_sen_slope_is_descriptive_and_handles_short_series():
    m=module()
    assert m.sen_slope([2000,2001,2002],[1,3,5])==2
    assert m.sen_slope([2000],[1]) is None


def test_equal_periods_reject_unequal_calendar_years():
    with pytest.raises(ValueError):module().equal_periods(2000,2002)
