import pandas as pd
import pytest

from earthquake_explorer.sections import SECTION_PRESETS, build_japan_section, build_section


def trench_layer():
    return {'features': [{
        'properties': {'Type': 'subduction', 'Name': 'PA\\OK'},
        'geometry': {'type': 'LineString', 'coordinates': [[143, 34], [143, 42]]},
    }]}


def catalogue(rows):
    return pd.DataFrame(rows, columns=['id', 'longitude', 'latitude', 'depth', 'region'])


def test_section_uses_a_finite_swath_and_keeps_negative_depth():
    japan = 'Japan and Kuril'
    frame = catalogue([
        ['near_a', 145, 38, 20, japan],
        ['near_b', 136, 38, 300, japan],
        ['beyond_a', 150, 38, 20, japan],
        ['beyond_b', 125, 38, 20, japan],
        ['outside_width', 140, 42, 20, japan],
        ['missing', 140, 38, None, japan],
        ['negative', 140, 38, -2, japan],
        ['other_region', 140, 38, 20, 'Other'],
    ])
    preset = dict(SECTION_PRESETS[0], reference_a=[146, 38], reference_b=[136, 38])
    result = build_section(frame, trench_layer(), preset)
    assert {row[0] for row in result['events']} == {'near_a', 'near_b', 'negative'}
    assert frame.loc[frame.id.eq('negative'), 'depth'].item() == -2
    assert result['origin'][0] == pytest.approx(143)
    assert result['distance_range_km'] == [-200, 1200]


def test_section_includes_endpoints_and_width_boundaries():
    empty = catalogue([])
    section = build_japan_section(empty, trench_layer())
    locations = [section['a']['coordinates'], section['b']['coordinates'], section['swath'][0], section['swath'][40]]
    frame = catalogue([[str(i), lon, lat, 10, 'Japan and Kuril'] for i, (lon, lat) in enumerate(locations)])
    result = build_japan_section(frame, trench_layer())
    assert len(result['events']) == 4
    assert result['events'][0][1] == pytest.approx(-200, abs=1e-5)
    assert result['events'][1][1] == pytest.approx(1200, abs=1e-5)
    assert abs(result['events'][2][2]) == pytest.approx(100, abs=1e-5)


def test_section_requires_a_matching_trench():
    with pytest.raises(ValueError, match='must cross'):
        build_japan_section(catalogue([]), {'features': []})


def test_section_crosses_the_date_line_without_selecting_greenwich():
    layer = {'features': [{
        'properties': {'Type': 'subduction', 'Name': 'TO/PA'},
        'geometry': {'type': 'LineString', 'coordinates': [[-174, -23], [-174, -17]]},
    }]}
    frame = catalogue([
        ['east', -173, -20, 10, 'Tonga Kermadec Fiji'],
        ['west', -179, -20, 100, 'Tonga Kermadec Fiji'],
        ['past_date_line', 179, -20, 400, 'Tonga Kermadec Fiji'],
        ['greenwich', 0, -20, 10, 'Tonga Kermadec Fiji'],
        ['outside_width', -179, -25, 10, 'Tonga Kermadec Fiji'],
    ])
    section = build_section(frame, layer, SECTION_PRESETS[2])
    assert {row[0] for row in section['events']} == {'east', 'west', 'past_date_line'}
    assert section['a']['coordinates'][0] < 0 < section['b']['coordinates'][0]
    assert section['map_longitude_range'][1] - section['map_longitude_range'][0] < 40
