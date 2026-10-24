import json
from collections import Counter
from pathlib import Path


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
