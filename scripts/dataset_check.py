"""
CLI utility to inspect Swiss road traffic accident GeoJSON datasets.

The script reports high-level integrity metrics, including duplicate checks,
feature counts, year coverage, geometry types, and the set of available
property keys. It supports running the same checks on the full dataset,
trimmed versions, or any other GeoJSON FeatureCollection that follows the
same schema.

Example usage:

    python scripts/dataset_check.py attached_assets/RoadTrafficAccidentLocations.json
    python scripts/dataset_check.py attached_assets/RoadTrafficAccidentLocations_last5years.json

You can specify multiple paths to compare outputs. By default the script
verifies duplicates using the `AccidentUID` property; override with
`--id-field` if needed, or disable with `--no-id-check`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect one or more accident GeoJSON datasets for integrity issues."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="GeoJSON file(s) to analyse.",
    )
    parser.add_argument(
        "--id-field",
        default="AccidentUID",
        help="Feature property used to detect duplicates (default: AccidentUID).",
    )
    parser.add_argument(
        "--no-id-check",
        action="store_true",
        help="Skip duplicate checks based on the id field.",
    )
    parser.add_argument(
        "--year-field",
        default="AccidentYear",
        help="Feature property storing the accident year (default: AccidentYear).",
    )
    parser.add_argument(
        "--max-duplicate-examples",
        type=int,
        default=5,
        help="Maximum number of duplicate IDs to display as examples.",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="Force printing every property key even for wide schemas.",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit with status 1 if duplicate IDs are detected.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Pretty-print JSON snippets (used only for malformed feature debug output).",
    )
    return parser.parse_args()


def load_geojson(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"[error] Failed to parse JSON from {path}: {exc}") from exc


def normalise_year(value: object, feature_index: int, year_field: str) -> Optional[int]:
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        print(
            f"[warn] Feature #{feature_index} has non-integer {year_field!r}: {value!r}",
            file=sys.stderr,
        )
        return None


def analyse_dataset(
    path: Path,
    id_field: Optional[str],
    year_field: str,
    max_duplicate_examples: int,
    list_keys: bool,
    indent: Optional[int],
) -> Tuple[int, bool]:
    if not path.exists():
        print(f"[error] File not found: {path}")
        return 0, False

    data = load_geojson(path)
    features: Iterable[dict] = data.get("features", [])
    total_features = 0
    geometry_types: Counter[str] = Counter()
    property_key_occurrences: Counter[str] = Counter()
    property_key_presence: set[str] = set()
    year_values: List[int] = []
    duplicate_map: Dict[str, List[int]] = defaultdict(list)
    missing_id_count = 0
    malformed_features = 0

    for idx, feature in enumerate(features):
        total_features += 1
        geometry = feature.get("geometry", {})
        geometry_type = geometry.get("type", "Unknown")
        geometry_types[geometry_type] += 1

        properties = feature.get("properties")
        if not isinstance(properties, dict):
            malformed_features += 1
            if indent is not None:
                print(
                    f"[warn] Feature #{idx} missing properties dict:\n"
                    f"{json.dumps(feature, indent=indent)[:500]}",
                    file=sys.stderr,
                )
            continue

        property_key_presence.update(properties.keys())
        property_key_occurrences.update(properties.keys())

        if year_field:
            year_value = normalise_year(properties.get(year_field), idx, year_field)
            if year_value is not None:
                year_values.append(year_value)

        if id_field:
            identifier = properties.get(id_field)
            if identifier in (None, ""):
                missing_id_count += 1
            else:
                duplicate_map[str(identifier)].append(idx)

    duplicates_detected = False
    duplicate_examples: List[Tuple[str, List[int]]] = []

    if id_field:
        for key, occurrences in duplicate_map.items():
            if len(occurrences) > 1:
                duplicates_detected = True
                if len(duplicate_examples) < max_duplicate_examples:
                    duplicate_examples.append((key, occurrences))

    dataset_size_mb = path.stat().st_size / (1024 * 1024)
    print("=" * 80)
    print(f"Dataset: {path}")
    print(f"Size: {dataset_size_mb:.2f} MB")
    print(f"Total features: {total_features}")

    if malformed_features:
        print(f"[warn] Malformed features (missing properties): {malformed_features}")

    if geometry_types:
        geometry_breakdown = ", ".join(
            f"{geom_type} ({count})" for geom_type, count in geometry_types.most_common()
        )
        print(f"Geometry types: {geometry_breakdown}")

    if property_key_presence:
        should_list_keys = list_keys or len(property_key_presence) <= 100
        print(f"Distinct property keys: {len(property_key_presence)}")
        if should_list_keys:
            sorted_keys = sorted(property_key_presence)
            print("Property keys:")
            for key in sorted_keys:
                occurrences = property_key_occurrences[key]
                print(f"  - {key} (present in {occurrences} features)")
        else:
            print(
                "Key list truncated (schema is wide). Use --list-keys to display every key."
            )

    if year_values:
        year_counter = Counter(year_values)
        min_year = min(year_values)
        max_year = max(year_values)
        print(f"Year range ({year_field}): {min_year} - {max_year}")
        print(f"Distinct years: {len(year_counter)}")
        top_years = ", ".join(
            f"{year}: {count}" for year, count in year_counter.most_common(10)
        )
        print(f"Year frequency (top 10): {top_years}")

    if id_field:
        print(f"ID field: {id_field}")
        duplicate_total = sum(len(indices) - 1 for indices in duplicate_map.values())
        print(f"Missing IDs: {missing_id_count}")
        print(f"Duplicate IDs: {duplicate_total}")
        if duplicate_examples:
            print("Duplicate examples:")
            for identifier, indices in duplicate_examples:
                print(f"  - {identifier} -> occurrences at feature indices {indices}")
        elif duplicate_total == 0:
            print("No duplicate IDs detected.")

    print("=" * 80)
    print()

    return total_features, duplicates_detected


def main() -> None:
    args = parse_args()
    any_duplicates = False
    total_processed = 0

    id_field = None if args.no_id_check else args.id_field

    for path in args.paths:
        total_features, duplicates_found = analyse_dataset(
            path=path,
            id_field=id_field,
            year_field=args.year_field,
            max_duplicate_examples=args.max_duplicate_examples,
            list_keys=args.list_keys,
            indent=args.indent,
        )
        total_processed += total_features
        any_duplicates |= duplicates_found

    print(f"Datasets analysed: {len(args.paths)}")
    print(f"Total features across inputs: {total_processed}")

    if any_duplicates and args.fail_on_duplicates:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
