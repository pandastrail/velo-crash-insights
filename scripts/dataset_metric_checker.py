"""
Dataset metric checker for Swiss road traffic accident GeoJSON files.

The script builds frequency indexes for each property in the dataset so you can
quickly inspect value distributions or get exact counts for specific values.

Examples:

    # Basic overview
    python scripts/dataset_metric_checker.py attached_assets/RoadTrafficAccidentLocations_last5years.json

    # Show the top accident severity categories
    python scripts/dataset_metric_checker.py attached_assets/RoadTrafficAccidentLocations_last5years.json \
        --value-count AccidentSeverityCategory_en

    # Count fatalities explicitly
    python scripts/dataset_metric_checker.py attached_assets/RoadTrafficAccidentLocations_last5years.json \
        --match "AccidentSeverityCategory_en=Accident with fatalities"
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect accident dataset metrics by building per-column value counts."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="GeoJSON file to analyse.",
    )
    parser.add_argument(
        "--value-count",
        action="append",
        dest="value_counts",
        default=[],
        help="Column to display value distribution for (can be passed multiple times).",
    )
    parser.add_argument(
        "--match",
        action="append",
        dest="matches",
        default=[],
        help="Exact equality check in the form column=value. Can be repeated.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum number of values to display for each --value-count column (default: 10).",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="List all property keys discovered in the dataset.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print dataset-wide summary (overrides other options).",
    )
    return parser.parse_args()


def load_features(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("features", [])


def build_index(features: Iterable[dict]) -> Tuple[int, Dict[str, Counter], Dict[str, int]]:
    value_counters: Dict[str, Counter] = defaultdict(Counter)
    missing_counts: Dict[str, int] = Counter()
    all_keys: set[str] = set()
    total_features = 0

    features_list: List[dict] = list(features)

    # Discover the union of property keys first.
    for feature in features_list:
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        all_keys.update(properties.keys())

    for feature in features_list:
        total_features += 1
        properties = feature.get("properties", {})

        for key in all_keys:
            if key not in properties:
                missing_counts[key] += 1

        if not isinstance(properties, dict):
            continue

        for key, value in properties.items():
            canonical_value = str(value)
            value_counters[key][canonical_value] += 1

    return total_features, value_counters, missing_counts


def print_summary(total_features: int, value_counters: Dict[str, Counter]) -> None:
    print("=" * 80)
    print("Dataset summary")
    print(f"Total records: {total_features}")
    print(f"Columns indexed: {len(value_counters)}")
    print("=" * 80)
    print()


def handle_value_counts(columns: List[str], counters: Dict[str, Counter], top: int, total: int) -> None:
    for column in columns:
        counter = counters.get(column)
        if not counter:
            print(f"[warn] Column '{column}' not found or has no values.")
            continue
        print(f"Value counts for '{column}' (top {top} of {len(counter)} unique values):")
        for value, count in counter.most_common(top):
            percentage = (count / total) * 100 if total else 0
            print(f"  {value!r}: {count} ({percentage:.2f}%)")
        print()


def parse_match(match_expression: str) -> Tuple[str, str]:
    if "=" not in match_expression:
        raise ValueError(f"Invalid match expression '{match_expression}'. Expected format column=value.")
    column, value = match_expression.split("=", 1)
    return column.strip(), value.strip()


def handle_matches(match_expressions: List[str], counters: Dict[str, Counter], total: int) -> None:
    for expression in match_expressions:
        try:
            column, value = parse_match(expression)
        except ValueError as exc:
            print(f"[error] {exc}")
            continue

        counter = counters.get(column)
        if counter is None:
            print(f"[warn] Column '{column}' not present in dataset.")
            continue

        count = counter.get(value, 0)
        percentage = (count / total) * 100 if total else 0
        print(f"Match '{column} = {value}': {count} records ({percentage:.2f}%)")
    if match_expressions:
        print()


def list_keys(counters: Dict[str, Counter], missing_counts: Dict[str, int], total: int) -> None:
    print("Indexed columns:")
    for column in sorted(counters.keys()):
        unique_values = len(counters[column])
        missing = missing_counts.get(column, 0)
        missing_percentage = (missing / total) * 100 if total else 0
        print(
            f"  - {column} (unique values: {unique_values}, missing: {missing} / "
            f"{total} - {missing_percentage:.2f}%)"
        )
    print()


def main() -> None:
    args = parse_args()

    if not args.path.exists():
        raise SystemExit(f"Input file not found: {args.path}")

    features = load_features(args.path)

    if not features:
        raise SystemExit("No features found in the dataset.")

    total_features, value_counters, missing_counts = build_index(features)

    print_summary(total_features, value_counters)

    if args.summary_only:
        return

    if args.list_keys or not args.value_counts and not args.matches:
        list_keys(value_counters, missing_counts, total_features)

    if args.value_counts:
        handle_value_counts(args.value_counts, value_counters, args.top, total_features)

    if args.matches:
        handle_matches(args.matches, value_counters, total_features)


if __name__ == "__main__":
    main()
