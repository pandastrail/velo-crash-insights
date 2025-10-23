"""
Utility to trim the Swiss road traffic accident dataset to the most recent N years.

Usage (defaults keep the latest five years):

    python scripts/orig_dataset_trim.py \
        --input attached_assets/RoadTrafficAccidentLocations.json \
        --output attached_assets/RoadTrafficAccidentLocations_last5years.json

The script loads the GeoJSON FeatureCollection, determines the most recent accident
year present, filters the features down to the requested number of trailing years,
then writes a new GeoJSON file with the reduced payload.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trim the accident dataset down to the most recent N years."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("attached_assets") / "RoadTrafficAccidentLocations.json",
        help="Path to the full GeoJSON dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("attached_assets")
        / "RoadTrafficAccidentLocations_last5years.json",
        help="Destination path for the trimmed GeoJSON dataset.",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Number of trailing years to keep (default: 5).",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Optional JSON indentation level for the output file.",
    )
    return parser.parse_args()


def extract_year(feature: dict) -> int:
    try:
        year_value = feature["properties"]["AccidentYear"]
    except KeyError as exc:
        raise ValueError("Feature missing AccidentYear in properties") from exc

    try:
        return int(year_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid AccidentYear value: {year_value!r}") from exc


def load_features(path: Path) -> Tuple[dict, List[dict], List[int]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    features: Iterable[dict] = data.get("features", [])

    extracted_features: List[dict] = []
    years: List[int] = []

    for feature in features:
        try:
            year = extract_year(feature)
        except ValueError as err:
            # Skip malformed entries but warn stderr for visibility.
            print(f"[warn] Skipping feature due to year parsing issue: {err}", file=sys.stderr)
            continue

        extracted_features.append(feature)
        years.append(year)

    if not extracted_features:
        raise ValueError("No valid features with AccidentYear found in dataset.")

    return data, extracted_features, years


def main() -> None:
    args = parse_args()

    if args.years <= 0:
        raise SystemExit("`--years` must be a positive integer.")

    if args.input == args.output:
        raise SystemExit("Input and output paths must be different.")

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    print(f"[info] Loading dataset from {args.input}")
    data, extracted_features, years = load_features(args.input)

    max_year = max(years)
    min_year_included = max_year - args.years + 1

    print(f"[info] Detected data range: {min(years)} - {max_year}")
    print(f"[info] Keeping records from {min_year_included} through {max_year}")

    trimmed_features = [
        feature
        for feature, year in zip(extracted_features, years)
        if year >= min_year_included
    ]

    kept_count = len(trimmed_features)
    dropped_count = len(extracted_features) - kept_count

    if kept_count == 0:
        raise SystemExit(
            "No features remain after trimming; check the `--years` value."
        )

    print(f"[info] Features kept: {kept_count}")
    print(f"[info] Features dropped: {dropped_count}")

    data["features"] = trimmed_features

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=args.indent)

    output_size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"[info] Wrote trimmed dataset to {args.output} ({output_size_mb:.2f} MB)")
    print("[info] Done.")


if __name__ == "__main__":
    main()
