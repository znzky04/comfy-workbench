"""A partial batch must remain observable without submitting duplicate prompts."""

from datetime import datetime, timedelta

import pytest

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.errors import JobError
from comfyui_agent_studio.models import GenerationRequest, JobStatus
from comfyui_agent_studio.service import GenerationService


@pytest.mark.parametrize("failure", [JobError("second submission failed"), KeyboardInterrupt()])
@pytest.mark.parametrize("use_wait", [False, True])
def test_accepted_prompt_is_persisted_before_second_submission(
    tmp_path, monkeypatch, failure, use_wait,
):
    settings = load_settings()
    settings.paths.manifest_root = tmp_path
    service = GenerationService(settings)

    class Backend:
        calls = 0

        def __init__(self, settings):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def health(self):
            pass

        def validate_workflow(self, graph):
            return []

        def submit(self, graph):
            self.calls += 1
            if self.calls == 2:
                saved = service.store.list_recent()[0]
                assert saved.prompt_ids == ["first-accepted"]
                assert saved.resolved_parameters["runs"][0]["seed"] == 0
                raise failure
            return "first-accepted"

        def history(self, prompt_id):
            return {"status": {"completed": True}, "outputs": {"image": True}}

        def output_paths(self, history):
            return [tmp_path / "retained.png"]

        def queue(self):
            return {"queue_running": []}

        def wait(self, prompt_id):
            return self.history(prompt_id)

        def close(self):
            pass

    monkeypatch.setattr("comfyui_agent_studio.service.ComfyClient", Backend)
    with pytest.raises(type(failure)):
        service.submit(GenerationRequest(
            workflow_id="anima.standard.v1", prompt="original adult character", seed=0, count=2,
        ))
    saved = service.store.list_recent()[0]
    assert saved.prompt_ids == ["first-accepted"]
    # Refresh only observes the accepted task, even after a process interruption.
    restored = GenerationService(settings)
    result = (
        restored.wait(saved.job_id) if use_wait and isinstance(failure, Exception)
        else restored.refresh(saved.job_id)
    )
    assert result.output_files == [str(tmp_path / "retained.png")]
    if isinstance(failure, Exception):
        assert result.status == JobStatus.FAILED
        assert result.error_category == "PartialSubmissionError"
    else:
        assert result.status == JobStatus.SUBMITTED
        with pytest.raises(JobError, match="批次提交尚未完成"):
            service.wait(saved.job_id)

        class FutureClock:
            @staticmethod
            def now(timezone):
                return datetime.now(timezone) + timedelta(hours=1)

        monkeypatch.setattr("comfyui_agent_studio.service.datetime", FutureClock)
        result = GenerationService(settings).refresh(saved.job_id)
        assert result.status == JobStatus.FAILED
        assert result.error_category == "IncompleteSubmission"
        assert result.output_files == [str(tmp_path / "retained.png")]
