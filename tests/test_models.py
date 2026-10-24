import pytest
from pydantic import ValidationError

from comfyui_agent_studio.models import GenerationRequest


def test_seed_zero_is_preserved() -> None:
    request = GenerationRequest(workflow_id="anima.standard.v1", prompt="test", seed=0)
    assert request.seed == 0


def test_minus_one_means_random_sentinel() -> None:
    request = GenerationRequest(workflow_id="anima.standard.v1", prompt="test", seed=-1)
    assert request.seed == -1


@pytest.mark.parametrize("field,value", [("width", 1025), ("height", 257)])
def test_dimensions_must_be_multiples_of_eight(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(workflow_id="anima.standard.v1", prompt="test", **{field: value})


def test_unknown_parameters_are_rejected() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(workflow_id="anima.standard.v1", prompt="test", mystery=True)
