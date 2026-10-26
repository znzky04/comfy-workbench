"""Offline tests must not depend on the developer's config or environment."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch):
    for name in (
        "COMFY_DEMO_COMFYUI_URL", "COMFY_DEMO_WORKSPACE", "COMFY_DEMO_OUTPUT_ROOT",
        "COMFY_DEMO_WEB_HOST", "COMFY_DEMO_WEB_PORT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("COMFY_DEMO_CONFIG", str(ROOT / "config.example.toml"))
