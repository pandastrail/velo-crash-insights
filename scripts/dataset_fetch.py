"""
CLI helper to download the public Swiss road traffic accident dataset.

Default command downloads the dataset into `attached_assets/RoadTrafficAccidentLocations.json`:

    python scripts/dataset_fetch.py

Specify `--output` for a different location, or `--url` if the upstream source changes.
Optionally compute a checksum by passing `--hash sha256`.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_URL = (
    "https://data.stadt-zuerich.ch/dataset/"
    "sid_dav_strassenverkehrsunfallorte/download/RoadTrafficAccidentLocations.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Swiss road traffic accident dataset from the public Zurich open data portal."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Source URL for the dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("attached_assets") / "RoadTrafficAccidentLocations.json",
        help="Destination path for the downloaded (and optionally decompressed) file.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4 * 1024 * 1024,
        help="Streaming chunk size in bytes (default: 4 MiB).",
    )
    parser.add_argument(
        "--hash",
        choices=("sha256", "md5"),
        default=None,
        help="Optional digest to compute while downloading.",
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Exit without downloading if the destination file already exists.",
    )
    parser.add_argument(
        "--decompress",
        action="store_true",
        help="Gunzip the downloaded file when the server serves gzip content (default: auto-detect).",
    )
    parser.add_argument(
        "--no-auto-decompress",
        action="store_true",
        help="Disable auto-detection based decompression even if the file looks gzipped.",
    )
    return parser.parse_args()


def format_size(num_bytes: int) -> str:
    for unit in ("bytes", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.2f} {unit}" if unit != "bytes" else f"{num_bytes} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} GB"


def sniff_is_gzip(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            signature = handle.read(2)
        return signature == b"\x1f\x8b"
    except OSError:
        return False


def gunzip_file(source: Path, destination: Path) -> None:
    with gzip.open(source, "rb") as compressed, destination.open("wb") as out:
        shutil.copyfileobj(compressed, out)


def download(url: str, output: Path, chunk_size: int, hash_name: str | None) -> Path:
    request = Request(url, headers={"User-Agent": "dataset-fetch/1.1"})

    try:
        response = urlopen(request)
    except HTTPError as exc:
        raise SystemExit(f"[error] HTTP error {exc.code} while downloading: {exc.reason}") from exc
    except URLError as exc:
        raise SystemExit(f"[error] Failed to reach server: {exc.reason}") from exc

    total_size = response.length or 0
    digest = hashlib.new(hash_name) if hash_name else None

    output.parent.mkdir(parents=True, exist_ok=True)

    bytes_downloaded = 0
    with output.open("wb") as handle:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            handle.write(chunk)
            bytes_downloaded += len(chunk)
            if digest:
                digest.update(chunk)
            print(
                f"\r[info] Downloaded {format_size(bytes_downloaded)}"
                + (f" / {format_size(total_size)}" if total_size else ""),
                end="",
                file=sys.stderr,
            )

    print(file=sys.stderr)  # Newline after progress output.

    if digest:
        print(f"[info] {hash_name.upper()} digest: {digest.hexdigest()}")

    final_size = output.stat().st_size
    print(f"[info] Saved dataset to {output} ({format_size(final_size)})")

    return output


def maybe_decompress(
    downloaded_path: Path, final_output: Path, force_decompress: bool, disable_auto: bool
) -> Path:
    # Determine whether to decompress.
    is_gzipped = sniff_is_gzip(downloaded_path)

    if not force_decompress and (disable_auto or not is_gzipped):
        # Either user disabled auto, or the file is already plain JSON.
        if downloaded_path != final_output:
            shutil.move(str(downloaded_path), str(final_output))
        return final_output

    print("[info] Detected gzip-compressed dataset. Decompressing...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        gunzip_file(downloaded_path, tmp_path)
        shutil.move(str(tmp_path), str(final_output))
    finally:
        if downloaded_path.exists():
            downloaded_path.unlink()
        if tmp_path.exists():
            tmp_path.unlink()

    final_size = final_output.stat().st_size
    print(f"[info] Decompressed dataset size: {format_size(final_size)}")
    return final_output


def main() -> None:
    args = parse_args()

    if args.chunk_size <= 0:
        raise SystemExit("`--chunk-size` must be a positive integer.")

    if args.skip_if_exists and args.output.exists():
        print(f"[info] Destination file already exists, skipping download: {args.output}")
        return

    print(f"[info] Downloading dataset from {args.url}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".download") as tmp_handle:
        tmp_path = Path(tmp_handle.name)

    downloaded_path = download(
        url=args.url,
        output=tmp_path,
        chunk_size=args.chunk_size,
        hash_name=args.hash,
    )

    maybe_decompress(
        downloaded_path=downloaded_path,
        final_output=args.output,
        force_decompress=args.decompress,
        disable_auto=args.no_auto_decompress,
    )


if __name__ == "__main__":
    main()
