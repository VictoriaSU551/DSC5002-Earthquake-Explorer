"""Shortest distance to PB2002 minor great-circle segments on a sphere.

This is spherical geodesy, not an ellipsoidal or geological error estimate.
No longitude/latitude degree pair is treated as Cartesian coordinates.
"""
import numpy as np

EARTH_RADIUS_KM = 6371.0088


def unit_vectors(longitude, latitude):
    lon, lat = np.deg2rad(longitude), np.deg2rad(latitude)
    return np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))


def geometry_lines(geojson):
    for feature in geojson['features']:
        geometry = feature['geometry']
        if geometry['type'] == 'LineString':
            yield np.asarray(geometry['coordinates'],dtype=float)[:,:2]
        elif geometry['type'] == 'MultiLineString':
            for line in geometry['coordinates']:
                yield np.asarray(line,dtype=float)[:,:2]
        elif geometry['type'] == 'Polygon':
            for line in geometry['coordinates']:
                yield np.asarray(line,dtype=float)[:,:2]
        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for line in polygon:
                    yield np.asarray(line,dtype=float)[:,:2]


def boundary_segments(geojson):
    pairs = [(line[:-1],line[1:]) for line in geometry_lines(geojson) if len(line)>1]
    if not pairs:
        raise ValueError('Boundary layer contains no line segments')
    a = np.concatenate([p[0] for p in pairs])
    b = np.concatenate([p[1] for p in pairs])
    a,b = unit_vectors(a[:,0],a[:,1]),unit_vectors(b[:,0],b[:,1])
    normal = np.cross(a,b)
    norm = np.linalg.norm(normal,axis=1)
    good = norm > 1e-12
    if not good.any():
        raise ValueError('Boundary layer contains only degenerate line segments')
    return a[good],b[good],normal[good]/norm[good,None]


def nearest_boundary_km(longitude, latitude, geojson, chunk_size=192):
    a,b,n = boundary_segments(geojson)
    points = unit_vectors(np.asarray(longitude),np.asarray(latitude))
    result = np.empty(len(points))
    cosine_arc = np.sum(a*b,axis=1)
    for start in range(0,len(points),chunk_size):
        q = points[start:start+chunk_size]
        da,db,dn = q@a.T,q@b.T,q@n.T
        # The perpendicular foot belongs to the minor arc iff it is forward
        # from a and backward from b. Otherwise the endpoint is closest.
        inside = (db-da*cosine_arc >= -1e-12) & (da-db*cosine_arc >= -1e-12)
        angle = np.arccos(np.clip(np.maximum(da,db),-1,1))
        cross_track = np.arcsin(np.clip(np.abs(dn),0,1))
        angle = np.where(inside,np.minimum(angle,cross_track),angle)
        result[start:start+len(q)] = np.min(angle,axis=1)*EARTH_RADIUS_KM
    return result


def epicentral_distance_km(longitude, latitude, anchor_lon, anchor_lat):
    lon,lat = np.deg2rad(longitude),np.deg2rad(latitude)
    x,y = np.deg2rad(anchor_lon),np.deg2rad(anchor_lat)
    h = np.sin((lat-y)/2)**2 + np.cos(lat)*np.cos(y)*np.sin((lon-x)/2)**2
    return 2*EARTH_RADIUS_KM*np.arcsin(np.sqrt(np.clip(h,0,1)))
