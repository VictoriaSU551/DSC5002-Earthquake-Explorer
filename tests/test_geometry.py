import importlib
import numpy as np
import pytest


def layer(coords):
    return {'features':[{'geometry':{'type':'LineString','coordinates':coords}}]}


def test_nearest_arc_handles_projection_and_endpoints():
    geo = importlib.import_module('earthquake_explorer.geometry')
    d = geo.nearest_boundary_km(np.array([5,20,5]), np.array([1,0,0]), layer([[0,0],[10,0]]))
    assert d == pytest.approx([111.19508,1111.9508,0], abs=0.0001)


def test_nearest_arc_crosses_date_line_without_crossing_greenwich():
    geo = importlib.import_module('earthquake_explorer.geometry')
    d = geo.nearest_boundary_km(np.array([180,0]), np.array([1,0]), layer([[170,0],[-170,0]]))
    assert d == pytest.approx([111.19508,18903.1636], abs=0.001)


def test_repeated_vertices_are_safe_and_empty_layer_is_rejected():
    geo = importlib.import_module('earthquake_explorer.geometry')
    assert geo.nearest_boundary_km([0],[0],layer([[0,0],[0,0],[10,0]]))[0] == pytest.approx(0,abs=0.001)
    with pytest.raises(ValueError):
        geo.nearest_boundary_km([0],[0],{'features':[]})


def test_arc_distance_matches_independent_dense_spherical_sampling():
    geo = importlib.import_module('earthquake_explorer.geometry')
    # Hand-picked arc with both longitude and latitude variation, 20k samples.
    lon1,lat1,lon2,lat2 = np.deg2rad([130,20,145,40])
    a = np.array([np.cos(lat1)*np.cos(lon1),np.cos(lat1)*np.sin(lon1),np.sin(lat1)])
    b = np.array([np.cos(lat2)*np.cos(lon2),np.cos(lat2)*np.sin(lon2),np.sin(lat2)])
    theta = np.arccos(a@b)
    t = np.linspace(0,1,20001)
    samples = (np.sin((1-t)*theta)[:,None]*a+np.sin(t*theta)[:,None]*b)/np.sin(theta)
    rng = np.random.default_rng(5002)
    lon,lat = rng.uniform(100,170,12),rng.uniform(-10,60,12)
    queries = np.column_stack([np.cos(np.deg2rad(lat))*np.cos(np.deg2rad(lon)),
        np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(lon)),np.sin(np.deg2rad(lat))])
    sampled = np.arccos(np.clip(np.max(queries@samples.T,axis=1),-1,1))*6371.0088
    exact = geo.nearest_boundary_km(lon,lat,layer([[130,20],[145,40]]))
    assert np.all(exact <= sampled+1e-6)
    assert np.max(sampled-exact)<0.12
