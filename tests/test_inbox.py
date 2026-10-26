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


def test_repeated_request_names_do_not_overwrite_evidence(tmp_path):
    watcher = InboxWatcher(FailingService(tmp_path))
    destinations = []
    for prompt in ("first", "second"):
        path = watcher.root / "pending" / "request.json"
        path.write_text(json.dumps({"workflow_id": "anima.standard.v1", "prompt": prompt}),
                        encoding="utf-8")
        destinations.append(Path(watcher.process_one(path)["request"]))
    assert destinations[0] != destinations[1]
    assert [json.loads(path.read_text())["prompt"] for path in destinations] == ["first", "second"]


def test_existing_processing_request_is_not_overwritten(tmp_path):
    watcher = InboxWatcher(FailingService(tmp_path))
    stale = watcher.root / "processing" / "request.json"
    stale.write_text("old interrupted request", encoding="utf-8")
    incoming = watcher.root / "pending" / "request.json"
    incoming.write_text(json.dumps({"workflow_id": "anima.standard.v1", "prompt": "new"}),
                        encoding="utf-8")
    watcher.process_one(incoming)
    assert stale.read_text(encoding="utf-8") == "old interrupted request"


def test_missing_claimed_request_does_not_crash_watcher(tmp_path):
    watcher = InboxWatcher(FailingService(tmp_path))
    result = watcher.process_one(watcher.root / "pending" / "missing.json")
    assert result["skipped"] is True
    assert not list((watcher.root / "processing").iterdir())


def test_orphan_error_evidence_is_not_overwritten(tmp_path):
    watcher = InboxWatcher(FailingService(tmp_path))
    evidence = watcher.root / "failed/request.json.error.json"
    evidence.write_text("old error evidence", encoding="utf-8")
    incoming = watcher.root / "pending/request.json"
    incoming.write_text(json.dumps({"workflow_id": "anima.standard.v1", "prompt": "new"}),
                        encoding="utf-8")
    result = watcher.process_one(incoming)
    assert Path(result["request"]).name != "request.json"
    assert evidence.read_text(encoding="utf-8") == "old error evidence"
