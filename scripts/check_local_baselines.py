"""Explicit local-only baseline verification; never modifies workflows or images."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / "workflows/source_manifest.json").read_text(encoding="utf-8"))
    tasks = json.loads((ROOT / "benchmarks/characters.json").read_text(encoding="utf-8"))["tasks"]
    checked = 0
    for item in manifest["workflows"]:
        path = args.source_root / item["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise SystemExit(f"Source hash mismatch: {path.name}")
        checked += 1
    references = 0
    for task in tasks:
        for name in task.get("input_images", []):
            path = args.reference_root / Path(name).name
            if hashlib.sha256(path.read_bytes()).hexdigest() != task["reference_sha256"]:
                raise SystemExit(f"Reference hash mismatch: {path.name}")
            references += 1
    print(f"PASS: {checked} source workflows and {references} reference bindings; read-only")


if __name__ == "__main__":
    main()
