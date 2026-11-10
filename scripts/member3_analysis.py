"""Reproduce the two RQ3 result CSVs from a built group dashboard."""

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import median


CLASSES = ("Shallow", "Intermediate", "Deep", "Missing")
REGION_COLUMNS = ("region", "known_depth_n", "missing_depth_n", "shallow_n",
                  "shallow_pct_known", "intermediate_n", "intermediate_pct_known",
                  "deep_n", "deep_pct_known", "median_depth_km")
SECTION_COLUMNS = ("region", "local_section", "half_width_km", "known_depth_n",
                   "shallow_n", "intermediate_n", "deep_n")


def read_catalogue(path):
    html = path.read_text(encoding="utf-8")
    _, marker, tail = html.partition('<script id="catalogue" type="application/json">')
    payload, end, _ = tail.partition("</script>")
    if not marker or not end:
        raise ValueError(f"No embedded catalogue found in {path}")
    data = json.loads(payload)
    if set(data["sections"]) != set(data["regions"]) or tuple(data["depth_names"]) != CLASSES:
        raise ValueError("Build the dashboard with the Member 3 RQ3 changes applied.")
    return data


def regional_row(label, events):
    counts = Counter(depth_class for _, depth_class in events)
    depths = [depth for depth, _ in events if depth is not None]
    known = len(depths)
    class_fields = []
    for name in CLASSES[:3]:
        n = counts[name]
        class_fields.extend((n, f"{100*n/known:.1f}" if known else ""))
    return (label, known, counts["Missing"], *class_fields,
            f"{median(depths):.1f}" if known else "")


def result_rows(data):
    names = data["regions"]
    events_by_region = defaultdict(list)
    event_by_id = {}
    for event in data["rows"]:
        event_id, depth, region, depth_class = event[0], event[4], names[event[7]], CLASSES[event[8]]
        events_by_region[region].append((depth, depth_class))
        event_by_id[event_id] = (region, depth_class)

    regions = [regional_row(name, events_by_region[name]) for name in names]
    regions.append(regional_row("All groups", [event for name in names for event in events_by_region[name]]))

    sections = []
    for name in names:
        section = data["sections"][name]
        ids = [entry[0] for entry in section["events"]]
        if len(set(ids)) != len(ids):
            raise ValueError(f"Duplicate event ID in the {name} cross section.")
        counts = Counter()
        for event_id in ids:
            region, depth_class = event_by_id[event_id]
            if region != name or depth_class == "Missing":
                raise ValueError(f"Unexpected event {event_id} in the {name} cross section.")
            counts[depth_class] += 1
        location = section["name"].partition(" | ")[0]
        sections.append((name, location, section["half_width_km"], len(ids),
                         *(counts[depth_class] for depth_class in CLASSES[:3])))
    return regions, sections


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dashboard", type=Path, help="Path to outputs/dashboard.html in the group project")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory for the two generated CSVs (default: beside this script)")
    args = parser.parse_args()
    regions, sections = result_rows(read_catalogue(args.dashboard))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "member3_region_summary.csv", REGION_COLUMNS, regions)
    write_csv(args.output_dir / "member3_section_summary.csv", SECTION_COLUMNS, sections)
    print(f"Exported {len(regions)-1} regions and {len(sections)} sections from {regions[-1][1]:,} known-depth events.")


if __name__ == "__main__":
    main()
