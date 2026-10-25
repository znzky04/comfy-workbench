from pathlib import Path

from comfyui_agent_studio.config import load_settings


def test_local_paths_resolve_under_project() -> None:
    settings = load_settings()
    assert settings.comfyui.lifecycle == "external"
    assert settings.retention.delete_generated_images is False
    assert settings.paths.workflow_root.is_absolute()
    assert settings.paths.manifest_root.is_absolute()
    assert settings.paths.workspace == Path("E:/AI/ComfyUI-Workspace/ComfyUI/ComfyUI")
    assert settings.paths.canonical_input_root == Path("E:/Comfy-Desktop/ComfyUI-Shared/input")
    assert settings.paths.canonical_output_root == Path(
        "E:/Comfy-Desktop/ComfyUI-Shared/output/comfyui-demo"
    )
