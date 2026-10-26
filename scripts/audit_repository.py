"""Read-only heuristic audit of reachable Git blobs and current source files.

Prints locations, never matched values. This is not a comprehensive secret scanner.
Reports belong in the ignored runs directory; do not publish them automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "provider_token": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{32,}|hf_[A-Za-z0-9]{30,})\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "credential_url": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
    "assigned_secret": re.compile(
        r'''(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)'''
        r'''\s*[=:]\s*["'][A-Za-z0-9_+/=.-]{20,}["']'''
    ),
}
LOCAL_PATH = re.compile(r"(?i)\b[A-Z]:[/\\](?:Users|AI|VibeCoding)[/\\]")
FORBIDDEN_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".safetensors", ".ckpt", ".zip"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def scan(payload: bytes, source: str) -> tuple[list[dict], bool]:
    if b"\0" in payload:
        return [], False
    content = payload.decode("utf-8", errors="replace")
    hits = [
        {"source": source, "line": content.count("\n", 0, match.start()) + 1, "rule": name}
        for name, pattern in RULES.items()
        for match in pattern.finditer(content)
    ]
    return hits, bool(LOCAL_PATH.search(content))


def audit() -> dict:
    objects = git("rev-list", "--objects", "--all").decode("utf-8").splitlines()
    identifiers = [line.split(" ", 1)[0] for line in objects]
    paths = {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in objects if " " in line}
    # Batch mode avoids spawning a process for every historical object.
    batch = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=ROOT,
        input=("\n".join(identifiers) + "\n").encode(), capture_output=True, check=True,
    ).stdout
    hits, local_paths, binaries = [], set(), set()
    cursor = blobs = 0
    for _ in identifiers:
        end = batch.index(b"\n", cursor)
        oid, kind, size = batch[cursor:end].decode().split()
        cursor = end + 1
        payload = batch[cursor:cursor + int(size)]
        cursor += int(size) + 1
        if kind != "blob":
            continue
        blobs += 1
        name = paths.get(oid, "unknown")
        found, local = scan(payload, f"history:{oid}:{name}")
        hits.extend(found)
        if local:
            local_paths.add(name)
        if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES:
            binaries.add(name)
    current_files = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    current_count = 0
    for raw in set(current_files.split(b"\0")) - {b""}:
        name = raw.decode("utf-8")
        path = ROOT / name
        if not path.is_file():
            continue
        current_count += 1
        found, local = scan(path.read_bytes(), f"worktree:{name}")
        hits.extend(found)
        if local:
            local_paths.add(name)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            binaries.add(name)
    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "reachable_blobs_checked": blobs,
        "current_files_checked": current_count,
        "secret_candidates": hits,
        "local_path_files": sorted(local_paths),
        "binary_candidates": sorted(binaries),
        "commit_author_identities": sorted(set(git("log", "--all", "--format=%an <%ae>")
                                              .decode("utf-8").splitlines())),
        "limitations": "Heuristics only; inspect provenance, prompts and commit identities manually.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "head", "reachable_blobs_checked", "current_files_checked", "secret_candidates",
        "binary_candidates", "limitations",
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
