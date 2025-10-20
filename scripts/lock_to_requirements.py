import sys
from pathlib import Path

try:
    import tomllib as toml  # Python 3.11+
except ModuleNotFoundError:
    import tomli as toml  # install tomli for older Pythons

in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("uv.lock")
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("requirements.txt")

data = toml.loads(in_path.read_text(encoding="utf-8"))
pkgs = []
for pkg in data.get("package", []):
    name = pkg.get("name")
    version = pkg.get("version")
    src = pkg.get("source", {})
    # skip virtual/local workspace entry
    if isinstance(src, dict) and src.get("virtual") == ".":
        continue
    if name and version:
        pkgs.append(f"{name}=={version}")

pkgs = sorted(dict.fromkeys(pkgs))  # dedupe, keep sorted
out_path.write_text("\n".join(pkgs) + ("\n" if pkgs else ""), encoding="utf-8")
print(f"Wrote {len(pkgs)} packages to {out_path}")