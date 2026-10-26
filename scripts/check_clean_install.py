"""Create an ignored source snapshot and fresh venv, then verify documented offline usage.

Uses package-index access to install dependencies, but never connects to ComfyUI or runs
generation. Keeps evidence and its environment under runs/public-readiness (no cleanup).
"""

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "runs/public-readiness" / f"clean-{uuid.uuid4().hex[:10]}"
    source = target / "source"
    source.mkdir(parents=True)
    files = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
    )
    for name in set(files.split(b"\0")) - {b""}:
        relative = Path(name.decode("utf-8"))
        original = ROOT / relative
        if original.is_file():
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
    assert not (source / "config.local.toml").exists()
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("COMFY_DEMO_") or name in {"PYTHONPATH", "PYTHONHOME"}:
            env.pop(name)
    temporary = target / "temp"
    temporary.mkdir()
    env.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary), PYTHONUTF8="1")
    venv = target / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], env=env, check=True)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    pip = [str(python), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
           "--no-cache-dir", "--timeout", "60", "--retries", "1",
           "--index-url", "https://pypi.org/simple"]
    commands = [
        [*pip, "hatchling>=1.27", "editables>=0.5"],
        [*pip, "--no-build-isolation", "-e", ".[web,dev]"],
        [str(python), "-m", "pytest", "-q"],
        [str(python), "-m", "ruff", "check", "src", "tests", "scripts", "examples"],
        [str(python), "examples/offline_review.py"],
        [str(python), "-m", "comfyui_agent_studio.cli", "workflow", "validate", "--all"],
    ]
    results = []
    for index, command in enumerate(commands):
        print(f"Checking {index + 1}/{len(commands)}: {' '.join(command[1:4])}", flush=True)
        with (target / f"step-{index + 1}.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=source, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, check=False, timeout=600)
        results.append({"command": command[1:], "returncode": result.returncode})
        (target / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        if result.returncode:
            raise SystemExit(f"Failed step {index + 1}; see {target}")
    # Verify project-relative resource lookup from outside the repository as well.
    subprocess.run([str(python), "-m", "comfyui_agent_studio.cli", "workflow", "list"],
                   cwd=target, env=env, check=True, stdout=subprocess.DEVNULL)
    print(f"PASS: clean editable installation and offline checks. Evidence: {target}")


if __name__ == "__main__":
    main()
