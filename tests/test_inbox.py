import json
from pathlib import Path
from types import SimpleNamespace

from comfyui_agent_studio.inbox import InboxWatcher


class FailingService:
    def __init__(self, root: Path):
        self.settings = SimpleNamespace(project_root=root)

    def submit(self, request, wait=False):
        raise RuntimeError("expected test failure")


def test_failed_request_and_error_evidence_are_retained(tmp_path: Path) -> None:
    watcher = InboxWatcher(FailingService(tmp_path))
    request = watcher.root / "pending" / "request.json"
    request.write_text(
        json.dumps(
            {
                "workflow_id": "anima.standard.v1",
                "prompt": "test",
                "client": "inbox",
            }
        ),
        encoding="utf-8",
    )
    result = watcher.process_one(request)
    failed = watcher.root / "failed" / "request.json"
    assert result["ok"] is False
    assert failed.is_file()
    assert failed.with_suffix(".json.error.json").is_file()
