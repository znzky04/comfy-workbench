from pathlib import Path

import pytest

from comfyui_agent_studio.client import ComfyClient
from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.errors import JobError


def test_cancel_removes_owned_queue_item_and_uses_targeted_interrupt(monkeypatch):
    calls = []
    monkeypatch.setattr(ComfyClient, "queue", lambda self: {"queue_running": [[0, "owned"]]})
    monkeypatch.setattr(ComfyClient, "_request", lambda self, method, path, **kwargs:
                        calls.append((method, path, kwargs)))
    with ComfyClient(load_settings()) as client:
        client.cancel("owned")
    assert calls == [
        ("POST", "/queue", {"json": {"delete": ["owned"]}}),
        ("POST", "/interrupt", {"json": {"prompt_id": "owned"}}),
    ]


@pytest.mark.parametrize("artifact", [
    {"filename": "image.png", "subfolder": "../../outside", "type": "output"},
    {"filename": "image.png", "type": "../outside"},
])
def test_history_artifact_cannot_escape_its_declared_root(tmp_path, artifact):
    settings = load_settings()
    settings.paths.canonical_output_root = tmp_path / "output/comfyui-demo"
    with ComfyClient(settings) as client, pytest.raises(JobError, match="输出路径"):
        client.output_paths({"outputs": {"1": {"images": [artifact]}}})


def test_valid_artifact_stays_in_shared_output(tmp_path):
    settings = load_settings()
    settings.paths.canonical_output_root = tmp_path / "output/comfyui-demo"
    with ComfyClient(settings) as client:
        paths = client.output_paths({"outputs": {"1": {"images": [
            {"filename": "image.png", "subfolder": "comfyui-demo/day", "type": "output"},
        ]}}})
    assert paths == [Path(tmp_path / "output/comfyui-demo/day/image.png")]
