import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", [
    "anima_studio.py", "inbox_watch.py", "run_comfy.py", "gen_from_their_workflow.py",
])
def test_legacy_exits_before_imports_or_side_effects(tmp_path, name):
    # -I removes project imports; the guard must run before third-party imports too.
    result = subprocess.run(
        [sys.executable, "-I", str(ROOT / "legacy" / name)],
        cwd=tmp_path, capture_output=True, timeout=5, check=False,
    )
    assert result.returncode == 1
    assert b"Traceback" not in result.stderr
    assert list(tmp_path.iterdir()) == []
