import json
import zipfile
from pathlib import Path

from comfyui_agent_studio.dsh import build_bundle, verify_bundle


def test_dsh_bundle_is_preset_v1_with_five_workflows(tmp_path: Path) -> None:
    path = build_bundle(tmp_path / "bundle.zip", version="test")
    report = verify_bundle(path)
    assert report["ok"] is True
    assert report["count"] == 5
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("preset.json"))
        assert manifest["format"] == "dsh-comfyui-workflow-preset"
        assert manifest["version"] == 1
        assert manifest["count"] == 5
        assert sum(item["requireSkill"] for item in manifest["workflows"]) == 3
        assert all(item["skill"] is not None for item in manifest["workflows"])


def test_mirror_bindings_are_exported_with_the_same_parameter_name(tmp_path: Path) -> None:
    path = build_bundle(tmp_path / "bundle.zip", version="test")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("preset.json"))
    hq = next(item for item in manifest["workflows"] if item["id"] == "anima.hq-2x.v1")
    seed_bindings = [item for item in hq["parameters"] if item["name"] == "seed"]
    assert {(item["nodeId"], item["inputKey"]) for item in seed_bindings} == {
        ("40", "seed"),
        ("80", "seed"),
    }
