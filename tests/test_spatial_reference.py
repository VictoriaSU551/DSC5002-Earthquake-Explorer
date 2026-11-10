import numpy as np
from earthquake_explorer.spatial_reference import sphere_reference,latitude_reference
from earthquake_explorer.geometry import nearest_boundary_km,EARTH_RADIUS_KM

def test_reference_equal_area_and_reproducible():
    lon,lat=sphere_reference(12,1)
    assert len(lon)==4096
    assert np.array_equal(lon,sphere_reference(12,1)[0])
    # Equal-area coordinates, not a uniform latitude distribution.
    assert abs(np.sin(np.radians(lat)).mean())<.001
    assert abs(np.mean(abs(lat)<=30)-.5)<.002
    assert abs(lon.mean())<.1

def test_latitude_control_preserves_empirical_support():
    _,lat=latitude_reference([-60,-20,20,60],10,4)
    assert set(lat)=={-60,-20,20,60}
    assert np.all(np.unique(lat,return_counts=True)[1]==256)

def test_arc_reference_distance_on_equatorial_segment():
    line={'features':[{'geometry':{'type':'LineString','coordinates':[[-80,0],[80,0]]}}]}
    d=nearest_boundary_km([0,0,0],[0,10,-30],line)
    assert np.allclose(d,np.radians([0,10,30])*EARTH_RADIUS_KM,atol=1e-7)
