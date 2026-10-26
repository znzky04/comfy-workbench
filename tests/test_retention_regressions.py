from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from typing import ClassVar

import pytest

from comfyui_agent_studio.client import ComfyClient
from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.errors import ComfyUnavailableError, JobError, WorkflowValidationError
from comfyui_agent_studio.models import GenerationRequest, JobStatus
from comfyui_agent_studio.registry import WorkflowRegistry
from comfyui_agent_studio.service import GenerationService


@pytest.fixture
def batch(tmp_path, monkeypatch):
    settings = load_settings()
    settings.paths.manifest_root = tmp_path / "runs"
    service = GenerationService(settings)
    job = service.create_manifest(GenerationRequest(
        workflow_id="anima.standard.v1", prompt="test", count=2,
    ))
    job.prompt_ids = ["first", "second"]
    job.prompt_id = "first"
    service.store.transition(job, JobStatus.SUBMITTED)
    service.store.transition(job, JobStatus.QUEUED)

    class Backend:
        histories: ClassVar[dict] = {
            "first": {"status": {"completed": True}, "outputs": ["first.png"]},
            "second": None,
        }
        cancelled: ClassVar[list] = []

        def __init__(self, settings):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def close(self):
            pass

        def history(self, prompt_id):
            return self.histories[prompt_id]

        def output_paths(self, history):
            return history.get("outputs", [])

        def queue(self):
            return {"queue_running": [[0, "second"]]}

        def cancel(self, prompt_id):
            self.cancelled.append(prompt_id)

        def wait(self, prompt_id):
            history = self.history(prompt_id)
            if history.get("status", {}).get("status_str") == "error":
                raise JobError("failed after producing an output")
            return history

    monkeypatch.setattr("comfyui_agent_studio.service.ComfyClient", Backend)
    return service, job, Backend


def test_refresh_keeps_outputs_after_remote_history_eviction(batch):
    service, job, backend = batch
    assert service.refresh(job.job_id).output_files == ["first.png"]
    backend.histories["first"] = None
    assert service.refresh(job.job_id).output_files == ["first.png"]


def test_cancel_keeps_completed_part_and_targets_unfinished_prompt(batch):
    service, job, backend = batch
    cancelled = service.cancel(job.job_id)
    assert cancelled.output_files == ["first.png"]
    assert cancelled.status == JobStatus.CANCELLED
    assert backend.cancelled == ["second"]


def test_cancel_does_not_relabel_already_completed_batch(batch):
    service, job, backend = batch
    backend.histories["second"] = {"status": {"completed": True}, "outputs": ["second.png"]}
    completed = service.cancel(job.job_id)
    assert completed.status == JobStatus.COMPLETED
    assert completed.output_files == ["first.png", "second.png"]
    assert backend.cancelled == []


def test_cancel_remains_recorded_when_followup_connection_is_lost(batch, monkeypatch):
    service, job, backend = batch
    original_history = backend.history

    def history(self, prompt_id):
        if self.cancelled:
            raise ComfyUnavailableError("connection lost after cancellation")
        return original_history(self, prompt_id)

    monkeypatch.setattr(backend, "history", history)
    result = service.cancel(job.job_id)
    assert result.status == JobStatus.CANCELLED
    assert result.output_files == ["first.png"]


def test_wait_failure_collects_partial_outputs_from_error_history(batch):
    service, job, backend = batch
    backend.histories["first"]["status"] = {"status_str": "error"}
    with pytest.raises(JobError):
        service.wait(job.job_id)
    failed = service.store.load(job.job_id)
    assert failed.status == JobStatus.FAILED
    assert failed.output_files == ["first.png"]


def test_wait_keeps_previously_recorded_output(batch):
    service, job, backend = batch
    job.output_files = ["previous.png"]
    service.store.save(job)
    backend.histories["second"] = {"status": {"completed": True}, "outputs": []}
    assert service.wait(job.job_id).output_files == ["previous.png", "first.png"]


def test_client_wait_observes_incomplete_history_instead_of_failing(monkeypatch):
    histories = iter([
        {"status": {"completed": False, "status_str": "running"}},
        {"status": {"completed": True}, "outputs": {}},
    ])
    monkeypatch.setattr(ComfyClient, "history", lambda *args: next(histories))
    monkeypatch.setattr("comfyui_agent_studio.client.time.sleep", lambda _: None)
    with ComfyClient(load_settings()) as client:
        assert client.wait("example", timeout_seconds=1)["status"]["completed"] is True


def test_current_img2img_rejects_multiple_references():
    request = GenerationRequest(
        workflow_id="larkie.img2img.v1", prompt="test", input_images=["one.png", "two.png"],
    )
    with pytest.raises(WorkflowValidationError, match="一张"):
        WorkflowRegistry().prepare(request, "example", 0, ["one.png", "two.png"])


def test_simultaneous_manifest_saves_use_separate_temporary_files(batch, monkeypatch):
    service, job, _ = batch
    import comfyui_agent_studio.manifests as module

    original_replace = module.os.replace
    barrier = Barrier(2)
    renames = Lock()

    def overlap(source, destination):
        barrier.wait(timeout=5)
        with renames:
            original_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", overlap)

    def save(label):
        copy = job.model_copy(deep=True)
        copy.request["prompt"] = label
        service.store.save(copy)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(save, ["left", "right"]))
    assert service.store.load(job.job_id).request["prompt"] in {"left", "right"}
