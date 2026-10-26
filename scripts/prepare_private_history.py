"""Prepare and verify an email-scrubbed mirror; never push or alter source refs.

Requires git-filter-repo in this interpreter. All backups/reports are ignored local
artifacts. Review the resulting mirror before explicitly updating any remote refs.
"""

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noreply", required=True)
    args = parser.parse_args()
    if not args.noreply.endswith("@users.noreply.github.com") or any(
        c in args.noreply for c in "\n\r<> "
    ):
        raise SystemExit("Expected a GitHub noreply address")
    if git("status", "--porcelain").strip():
        raise SystemExit("Commit reviewed engineering changes first; source worktree must be clean")
    target = ROOT / "runs/public-readiness" / f"history-{uuid.uuid4().hex[:10]}"
    target.mkdir(parents=True)
    backup = target / "before.bundle"
    git("bundle", "create", str(backup), "--all")
    git("bundle", "verify", str(backup))
    mirror = target / "cleaned.git"
    git("clone", "--mirror", "--no-hardlinks", str(ROOT), str(mirror))
    emails = set(git("log", "--all", "--format=%ae%n%ce").decode().splitlines())
    # Do not silently attribute another contributor's work to this maintainer.
    old = {email for email in emails if email != args.noreply}
    if len(old) > 1:
        raise SystemExit(f"Found multiple identities; inspect private backup and map explicitly: {target}")
    mailmap = target / "mailmap.private"
    mailmap.write_text("".join(f"<{args.noreply}> <{email}>\n" for email in sorted(old)),
                       encoding="utf-8")
    before = git("rev-parse", "main").decode().strip()
    tree = git("rev-parse", "main^{tree}").decode().strip()
    subprocess.run([sys.executable, "-m", "git_filter_repo", "--force", "--mailmap", str(mailmap)],
                   cwd=mirror, check=True)
    assert git("rev-parse", "main^{tree}", cwd=mirror).decode().strip() == tree
    after = git("rev-parse", "main", cwd=mirror).decode().strip()
    identities = set(git("log", "--all", "--format=%ae%n%ce", cwd=mirror).decode().splitlines())
    assert identities == {args.noreply}
    assert git("rev-list", "--count", "main") == git("rev-list", "--count", "main", cwd=mirror)
    assert git("rev-parse", "main").decode().strip() == before
    report = {
        "source_main": before, "cleaned_main": after, "tree": tree,
        "commit_count": int(git("rev-list", "--count", "main")),
        "identities": sorted(identities), "identical_main_tree": True,
        "backup_bundle_verified": True, "source_refs_changed": False, "pushed": False,
        "mirror": str(mirror),
    }
    (target / "review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
