"""Finite regional sections, with a shared trench origin and sampling window."""
import numpy as np

from .geometry import EARTH_RADIUS_KM, geometry_lines, unit_vectors


SECTION_PRESETS = [
    {
        'region': 'Japan and Kuril', 'name': 'Northern Tohoku | Japan Trench',
        'reference_a': [146, 39.5], 'reference_b': [135, 42.5], 'boundaries': ['PA\\OK'],
        'trench_name': 'Japan Trench',
        'a_place': 'Pacific Ocean east of northeast Japan',
        'b_place': 'Wangqing County, Jilin, northeast China',
        'map_labels': [[135, 39, 'Sea of Japan'], [147, 37, 'Pacific Ocean'], [141, 41.5, 'Northern Japan']],
        'reference': 'https://pubs.usgs.gov/of/2010/1083/d/',
    },
    {
        'region': 'Indonesia and Philippines', 'name': 'East Java | Sunda-Java Trench',
        'reference_a': [111.5, -12.5], 'reference_b': [114, -4.5], 'boundaries': ['SU/AU'],
        'trench_name': 'Sunda-Java Trench',
        'a_place': 'Indian Ocean south of East Java', 'b_place': 'Borneo interior, Indonesia',
        'map_labels': [[114, -7.5, 'Java'], [114, -5, 'Java Sea'], [114, -12, 'Indian Ocean']],
        'reference': 'https://www.usgs.gov/publications/seismicity-earth-1900-2012-java-and-vicinity',
    },
    {
        'region': 'Tonga Kermadec Fiji', 'name': 'Central Tonga | Tonga Trench',
        'reference_a': [-172, -20], 'reference_b': [178, -20], 'boundaries': ['TO/PA'],
        'trench_name': 'Tonga Trench',
        'a_place': 'Pacific Ocean east of Tonga', 'b_place': 'Fiji region, west of Tonga',
        'map_labels': [[178.5, -17.5, 'Fiji'], [-173, -18, 'Tonga']],
        'reference': 'https://pubs.usgs.gov/of/2010/1083/i/',
    },
    {
        'region': 'Andes', 'name': 'Northern Chile | Peru-Chile Trench',
        'reference_a': [-77.5, -24], 'reference_b': [-68, -24], 'boundaries': ['NZ\\SA'],
        'trench_name': 'Peru-Chile Trench',
        'a_place': 'Pacific Ocean west of northern Chile', 'b_place': 'Presidente Hayes, Paraguayan Chaco',
        'map_labels': [[-69, -26, 'Chile'], [-65, -26, 'Argentina'], [-74, -27, 'Pacific Ocean']],
        'reference': 'https://pubs.usgs.gov/of/2015/1031/e/',
    },
    {
        'region': 'Alaska and Aleutians', 'name': 'Central Aleutians | Aleutian Trench',
        'reference_a': [-174, 48], 'reference_b': [-174, 56], 'boundaries': ['NA/PA'],
        'trench_name': 'Aleutian Trench',
        'a_place': 'North Pacific Ocean south of the Aleutians', 'b_place': 'Bering Sea north of the Aleutians',
        'map_labels': [[-170, 53, 'Aleutian Islands'], [-171, 58, 'Bering Sea']],
        'reference': 'https://www.usgs.gov/publications/seismicity-earth-1900-2010-aleutian-arc-and-vicinity',
    },
    {
        'region': 'Mediterranean and Himalaya', 'name': 'Western Crete | Hellenic Arc',
        'reference_a': [24, 32], 'reference_b': [24, 40], 'boundaries': ['AS/AF'],
        'trench_name': 'Hellenic subduction boundary',
        'a_place': 'Mediterranean Sea south of Crete', 'b_place': 'Southern Carpathians, Romania',
        'map_labels': [[25.5, 37, 'Aegean Sea'], [25.5, 35.3, 'Crete']],
        'reference': 'https://pubs.usgs.gov/of/2010/1083/q/',
    },
    {
        'region': 'Other', 'name': 'Southern Hikurangi, New Zealand | Local example',
        'reference_a': [179, -41], 'reference_b': [173, -41], 'boundaries': ['KE/PA'],
        'trench_name': 'Hikurangi margin',
        'a_place': 'Pacific Ocean east of southern North Island, New Zealand',
        'b_place': 'Tasman Sea west of New Zealand',
        'map_labels': [[174, -43, 'New Zealand'], [170, -39, 'Tasman Sea']],
        'reference': 'https://www.usgs.gov/publications/upper-plate-heterogeneity-along-southern-hikurangi-margin-new-zealand',
        'scope_note': 'Other is a global residual category; this section covers only southern Hikurangi, New Zealand.',
    },
]


def coordinates(vectors):
    vectors = np.asarray(vectors)
    return np.column_stack((
        np.rad2deg(np.arctan2(vectors[:, 1], vectors[:, 0])),
        np.rad2deg(np.arctan2(vectors[:, 2], np.hypot(vectors[:, 0], vectors[:, 1]))),
    )).tolist()


def build_section(frame, boundaries, preset):
    endpoints = np.asarray([preset['reference_a'], preset['reference_b']])
    reference_a, reference_b = unit_vectors(endpoints[:, 0], endpoints[:, 1])
    normal = np.cross(reference_a, reference_b)
    normal_length = np.linalg.norm(normal)
    reference_angle = np.arctan2(normal_length, reference_a @ reference_b)
    normal /= normal_length
    reference_tangent = np.cross(normal, reference_a)
    trench_lines = [line for feature in boundaries['features']
                    if feature['properties'].get('Type') == 'subduction'
                    and feature['properties'].get('Name') in preset['boundaries']
                    for line in geometry_lines({'features': [feature]})]
    crossings = []
    for line in trench_lines:
        points = unit_vectors(line[:, 0], line[:, 1])
        for start, end in zip(points[:-1], points[1:]):
            intersection = np.cross(np.cross(start, end), normal)
            length = np.linalg.norm(intersection)
            if length < 1e-12:
                continue
            arc = np.arccos(np.clip(start @ end, -1, 1))
            for point in [intersection / length, -intersection / length]:
                angles = np.arccos(np.clip([start @ point, point @ end], -1, 1))
                along = np.arctan2(point @ reference_tangent, point @ reference_a)
                if abs(angles.sum() - arc) < 1e-8 and 0 < along < reference_angle:
                    crossings.append(point)
    if not crossings:
        raise ValueError(preset['name'] + ': route must cross the selected PB2002 subduction boundary.')
    origin = crossings[0]
    if any(np.linalg.norm(point - origin) > 1e-6 for point in crossings[1:]):
        raise ValueError(preset['name'] + ': route has multiple trench intersections.')
    tangent = np.cross(normal, origin)
    lower, upper, half_width = -200, 1200, 100

    def surface_points(along, offset=0):
        angle = np.asarray(along) / EARTH_RADIUS_KM
        centre = np.cos(angle)[:, None] * origin + np.sin(angle)[:, None] * tangent
        return centre * np.cos(offset / EARTH_RADIUS_KM) + normal * np.sin(offset / EARTH_RADIUS_KM)

    route_distances = np.linspace(lower, upper, 81)
    left = surface_points(route_distances, half_width)
    right = surface_points(route_distances[::-1], -half_width)
    swath = coordinates(np.vstack((left, right, left[:1])))
    endpoints = coordinates(surface_points([lower, upper]))

    eligible = frame.loc[frame.region.eq(preset['region']) & frame.depth.notna()]
    points = unit_vectors(eligible.longitude.to_numpy(), eligible.latitude.to_numpy())
    along = EARTH_RADIUS_KM * np.arctan2(points @ tangent, points @ origin)
    offset = EARTH_RADIUS_KM * np.arcsin(np.clip(points @ normal, -1, 1))
    inside = (along >= lower - 1e-6) & (along <= upper + 1e-6) & (np.abs(offset) <= half_width + 1e-6)
    centre_longitude = coordinates(origin[None, :])[0][0]
    map_points = np.asarray(swath)
    map_points[:, 0] = centre_longitude + (map_points[:, 0] - centre_longitude + 180) % 360 - 180
    map_lower = map_points.min(axis=0) - [1.5, 1.5]
    map_upper = map_points.max(axis=0) + [1.5, 1.5]
    centre = (map_lower + map_upper) / 2
    span = map_upper - map_lower
    latitude_scale = np.cos(np.deg2rad(centre[1]))
    longitude_span = max(span[0], span[1] * .9 / latitude_scale)
    latitude_span = max(span[1], span[0] * latitude_scale / .9)
    map_lower = centre - np.array([longitude_span, latitude_span]) / 2
    map_upper = centre + np.array([longitude_span, latitude_span]) / 2
    width_checks = []
    for width in [50, 100, 200]:
        mask = (along >= lower - 1e-6) & (along <= upper + 1e-6) & (np.abs(offset) <= width + 1e-6)
        depths = eligible.depth.to_numpy()[mask]
        width_checks.append({'half_width_km': width, 'known': len(depths),
                             'shallow': int((depths < 70).sum()),
                             'intermediate': int(((depths >= 70) & (depths < 300)).sum()),
                             'deep': int((depths >= 300).sum())})
    return {
        'region': preset['region'], 'name': preset['name'],
        'a': {'coordinates': endpoints[0], 'place': preset['a_place']},
        'b': {'coordinates': endpoints[1], 'place': preset['b_place']},
        'origin': coordinates(origin[None, :])[0],
        'central_longitude': centre_longitude, 'trench_name': preset['trench_name'],
        'map_labels': preset.get('map_labels', []),
        'map_longitude_range': [float(map_lower[0]), float(map_upper[0])],
        'map_latitude_range': [float(map_lower[1]), float(map_upper[1])],
        'distance_range_km': [lower, upper], 'depth_range_km': [-10, 720],
        'half_width_km': half_width, 'route': coordinates(surface_points(route_distances)),
        'swath': swath, 'trench': [line.tolist() for line in trench_lines],
        'events': [[event_id, round(float(distance), 6), round(float(cross), 6)]
                   for event_id, distance, cross in zip(eligible.id[inside], along[inside], offset[inside])],
        'width_checks': width_checks, 'reference': preset['reference'],
        'method': 'PB2002 boundary crossing = 0 km. A is 200 km seaward; B is 1,200 km toward the overriding side. '
                  'Events use the selected catalogue region and a 100 km half-width. '
                  + preset.get('scope_note', 'This is a local section within ' + preset['region'] + '.'),
    }


def build_japan_section(frame, boundaries):
    return build_section(frame, boundaries, SECTION_PRESETS[0])


def build_sections(frame, boundaries):
    return {preset['region']: build_section(frame, boundaries, preset) for preset in SECTION_PRESETS}
