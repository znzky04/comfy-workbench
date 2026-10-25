import json
from pathlib import Path

import pytest

from comfyui_agent_studio.errors import WorkflowValidationError
from comfyui_agent_studio.manifests import ManifestStore
from comfyui_agent_studio.models import GenerationRequest
from comfyui_agent_studio.registry import WorkflowRegistry, sha256_file


def test_all_registered_workflows_pass_static_validation() -> None:
    result = WorkflowRegistry().validate_all()
    assert set(result) == {
        "anima.standard.v1",
        "anima.hq-2x.v1",
        "animagine.standard.v1",
        "larkie.img2img.v1",
        "larkie.incontext.v1",
    }
    assert all(not errors for errors in result.values()), result


def test_seed_zero_and_output_prefix_are_applied() -> None:
    registry = WorkflowRegistry()
    request = GenerationRequest(
        workflow_id="anima.standard.v1",
        prompt="hello",
        seed=0,
        output_label="unit test",
    )
    _, workflow, resolved = registry.prepare(request, "job-1", 0)
    assert workflow["40"]["inputs"]["seed"] == 0
    assert resolved["seed"] == 0
    assert workflow["60"]["inputs"]["filename_prefix"].endswith("unit_test_job-1_0_1")


def test_hq_parameters_are_mirrored() -> None:
    registry = WorkflowRegistry()
    request = GenerationRequest(
        workflow_id="anima.hq-2x.v1", prompt="hello", seed=7, steps=31, cfg=4.5
    )
    _, workflow, _ = registry.prepare(request, "job-2", 0)
    assert workflow["40"]["inputs"]["seed"] == workflow["80"]["inputs"]["seed"] == 7
    assert workflow["40"]["inputs"]["steps"] == workflow["80"]["inputs"]["steps"] == 31
    assert workflow["40"]["inputs"]["cfg"] == workflow["80"]["inputs"]["cfg"] == 4.5


def test_incontext_requires_reference_image() -> None:
    request = GenerationRequest(workflow_id="larkie.incontext.v1", prompt="hello")
    with pytest.raises(WorkflowValidationError, match="必须提供参考图"):
        WorkflowRegistry().prepare(request, "job-3", 0)


def test_source_canvas_manifest_matches_files() -> None:
    manifest_path = Path("workflows/source_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_root = Path(manifest["source_root"])
    assert len(manifest["workflows"]) == 12
    for item in manifest["workflows"]:
        path = source_root / item["filename"]
        assert path.is_file()
        assert sha256_file(path) == item["sha256"]


@pytest.mark.parametrize("negative", [None, "", "模糊, watermark\n多余手指"])
def test_prompt_history_preserves_effective_defaults_and_overrides(tmp_path, negative) -> None:
    from comfyui_agent_studio.config import load_settings
    from comfyui_agent_studio.service import GenerationService

    settings = load_settings()
    settings.paths.manifest_root = tmp_path
    service = GenerationService(settings)
    request = GenerationRequest(
        workflow_id="anima.standard.v1",
        prompt="小云雀来海\nmoonlit street",
        negative_prompt=negative,
    )
    manifest = service.create_manifest(request)
    definition, graph, resolved = service.registry.prepare(request, manifest.job_id, 0)
    binding = definition.parameters["negative_prompt"]
    assert resolved["negative_prompt"] == graph[binding.node_id]["inputs"][binding.input]
    if negative is not None:
        assert resolved["negative_prompt"] == negative
    manifest.resolved_parameters = {"runs": [resolved]}
    service.store.save(manifest)
    loaded = ManifestStore(tmp_path).load(manifest.job_id)
    assert loaded.request["prompt"] == request.prompt
    assert loaded.resolved_parameters["runs"][0]["prompt"] == request.prompt
    assert loaded.resolved_parameters["runs"][0]["negative_prompt"] == resolved["negative_prompt"]
