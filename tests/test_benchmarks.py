import json
from collections import Counter
from pathlib import Path

from comfyui_agent_studio.models import GenerationRequest

REQUEST_FIELDS = {
    "workflow_id",
    "prompt",
    "negative_prompt",
    "seed",
    "count",
    "width",
    "height",
    "steps",
    "cfg",
    "denoise",
    "input_images",
    "output_label",
    "client",
}


def test_character_benchmark_is_exactly_two_three_three() -> None:
    data = json.loads(Path("benchmarks/characters.json").read_text(encoding="utf-8"))
    tasks = data["tasks"]
    assert len(tasks) == 8
    assert Counter(item["category"] for item in tasks) == {
        "larkie": 2,
        "fan-character": 3,
        "original": 3,
    }
    assert {item["workflow_id"] for item in tasks} == {
        "anima.standard.v1",
        "anima.hq-2x.v1",
        "animagine.standard.v1",
        "larkie.img2img.v1",
        "larkie.incontext.v1",
    }
    assert "非商业同人技术评测" in data["public_fan_character_notice"]


def test_all_benchmark_requests_match_generation_contract() -> None:
    data = json.loads(Path("benchmarks/characters.json").read_text(encoding="utf-8"))
    defaults = data["defaults"]
    for task in data["tasks"]:
        payload = {**defaults, **task, "client": task["assigned_client"]}
        request = GenerationRequest.model_validate(
            {key: value for key, value in payload.items() if key in REQUEST_FIELDS}
        )
        assert request.workflow_id == task["workflow_id"]
        if task.get("requires_reference"):
            assert request.input_images
            assert len(task["reference_sha256"]) == 64
            int(task["reference_sha256"], 16)
