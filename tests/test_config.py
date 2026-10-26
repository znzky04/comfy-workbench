from pathlib import Path

import pytest

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.errors import ConfigurationError


def test_local_paths_resolve_under_project() -> None:
    settings = load_settings()
    assert settings.comfyui.lifecycle == "external"
    assert settings.retention.delete_generated_images is False
    assert settings.paths.workflow_root.is_absolute()
    assert settings.paths.manifest_root.is_absolute()
    instance = (settings.project_root / "../ComfyUI").resolve()
    assert settings.paths.workspace == instance
    assert settings.paths.canonical_input_root == instance / "input"
    assert settings.paths.canonical_output_root == instance / "output/comfyui-demo"


def test_paths_do_not_change_with_shell_directory(tmp_path, monkeypatch):
    before = load_settings()
    monkeypatch.chdir(tmp_path)
    after = load_settings()
    assert after.paths == before.paths


def test_explicit_config_and_environment_override(tmp_path, monkeypatch):
    config = tmp_path / "custom.toml"
    config.write_text('[paths]\nworkspace="instance"\n[web]\nport=8200\n', encoding="utf-8")
    monkeypatch.setenv("COMFY_DEMO_CONFIG", str(config))
    monkeypatch.setenv("COMFY_DEMO_WEB_PORT", "8201")
    settings = load_settings()
    assert settings.paths.workspace == settings.project_root / "instance"
    assert settings.web.port == 8201
    with pytest.raises(ConfigurationError, match="配置文件不存在"):
        load_settings(Path("missing-public-config.toml"))
