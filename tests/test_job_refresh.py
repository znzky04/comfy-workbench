from datetime import datetime, timedelta

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.models import GenerationRequest, JobStatus
from comfyui_agent_studio.service import GenerationService


def setup_service(tmp_path, monkeypatch, history=None, running=True):
    settings = load_settings()
    settings.paths.manifest_root = tmp_path / "runs"
    service = GenerationService(settings)
    manifest = service.create_manifest(
        GenerationRequest(
            workflow_id="anima.standard.v1",
            prompt="test",
            client="studio",
        )
    )
    manifest.prompt_id = "remote-prompt"
    manifest.prompt_ids = ["remote-prompt"]
    service.store.transition(manifest, JobStatus.SUBMITTED)
    service.store.transition(manifest, JobStatus.QUEUED)
    cancelled = []

    class Backend:
        def __init__(self, settings):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def history(self, prompt_id):
            return history

        def queue(self):
            return {"queue_running": [[0, "remote-prompt"]] if running else []}

        def cancel(self, prompt_id):
            cancelled.append(prompt_id)

        def output_paths(self, history):
            return ["retained-first-output.png"] if history.get("outputs") else []

    monkeypatch.setattr("comfyui_agent_studio.service.ComfyClient", Backend)
    return service, manifest, cancelled


def test_restart_reconciles_persisted_queue_without_resubmitting(tmp_path, monkeypatch):
    service, manifest, _ = setup_service(tmp_path, monkeypatch)
    # A new service instance represents a restart; the remote prompt is unchanged.
    restarted = GenerationService(service.settings)
    assert restarted.refresh(manifest.job_id).status == JobStatus.RUNNING
    assert restarted.store.load(manifest.job_id).prompt_ids == ["remote-prompt"]


def test_failed_remote_execution_keeps_detail(tmp_path, monkeypatch):
    service, manifest, _ = setup_service(
        tmp_path,
        monkeypatch,
        history={
            "status": {
                "status_str": "error",
                "messages": [["execution_error", {"message": "broken node"}]],
            },
        },
    )
    failed = service.refresh(manifest.job_id)
    assert failed.status == JobStatus.FAILED
    assert "broken node" in failed.error_detail


def test_timeout_records_failure_without_interrupting_server(tmp_path, monkeypatch):
    service, manifest, cancelled = setup_service(tmp_path, monkeypatch, running=False)

    class FutureClock:
        @staticmethod
        def now(timezone):
            return datetime.now(timezone) + timedelta(hours=1)

    monkeypatch.setattr("comfyui_agent_studio.service.datetime", FutureClock)
    failed = service.refresh(manifest.job_id)
    assert failed.status == JobStatus.FAILED
    assert failed.error_category == "JobTimeout"
    assert cancelled == []


def test_cancel_only_targets_owned_prompt_and_is_idempotent(tmp_path, monkeypatch):
    service, manifest, cancelled = setup_service(tmp_path, monkeypatch)
    assert service.cancel(manifest.job_id).status == JobStatus.CANCELLED
    assert service.cancel(manifest.job_id).status == JobStatus.CANCELLED
    assert service.refresh(manifest.job_id).status == JobStatus.CANCELLED
    assert cancelled == ["remote-prompt"]


def test_failure_preserves_any_already_generated_outputs(tmp_path, monkeypatch):
    service, manifest, _ = setup_service(
        tmp_path,
        monkeypatch,
        history={
            "status": {"status_str": "error"},
            "outputs": {"completed_image": True},
        },
    )
    failed = service.refresh(manifest.job_id)
    assert failed.status == JobStatus.FAILED
    assert failed.output_files == ["retained-first-output.png"]
