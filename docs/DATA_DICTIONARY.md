# Analysis data dictionary

`data/processed/earthquakes.csv` has one row per retained USGS preferred earthquake event. Units are degrees, kilometres and UTC unless indicated.

| Field | Meaning |
| --- | --- |
| id | Stable USGS event ID used for deduplication and case membership |
| time | Preferred origin timestamp in UTC |
| latitude | Epicentre latitude, −90 to 90 degrees |
| longitude | Epicentre longitude, −180 to 180 degrees; date-line crossings handled explicitly |
| depth | Preferred hypocentre depth in km; missing and negative reported values retained |
| mag | Preferred catalogue magnitude; M≥5; magnitude types are mixed |
| magType | Original preferred magnitude scale label, e.g. mw/mww/mb |
| place | Original catalogue location description; not used to assign regions |
| status | Catalogue review status, retained without imposing a reviewed-only filter |
| updated | Last preferred-record update time, used to resolve repeated IDs |
| type | Source event type; retained observations must be earthquake |
| year | Calendar year of UTC origin time |
| region | First matching priority-ordered geographic box in config.json, otherwise Other |
| depth_class | Shallow (<70), Intermediate (70–<300), Deep (≥300), or Missing |
| negative_depth | Boolean audit flag; a negative depth is not automatically excluded |
| magnitude_band | [5,6), [6,7), [7,8), or [8,∞) |
| boundary_distance_km | Shortest spherical distance to any PB2002 minor great-circle segment, R=6371.0088 km |

Case-membership CSVs add `relative_days` (fractional days relative to the exact anchor timestamp) and `anchor_distance_km` (spherical epicentral separation). Source CSVs retain all returned service fields, including quality fields not used in this baseline.

Summary missingness uses each variable's full analysis-population denominator. Regional deep-event percentages use known depths only. Boundary-within-distance percentages use all valid coordinate events. Spearman sample sizes use pairwise nonmissing observations. All these denominators are explicit in the saved tables and report.
