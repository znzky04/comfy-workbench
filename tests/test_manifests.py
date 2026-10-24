from pathlib import Path

import pytest

from comfyui_agent_studio.errors import JobError
from comfyui_agent_studio.manifests import ManifestStore
from comfyui_agent_studio.models import JobManifest, JobStatus


def make_manifest() -> JobManifest:
    return JobManifest(
        job_id="unit-job",
        client="cli",
        workflow_id="anima.standard.v1",
        workflow_version="1.0.0",
        workflow_sha256="a" * 64,
        request={"prompt": "test"},
    )


def test_manifest_is_written_atomically(tmp_path: Path) -> None:
    store = ManifestStore(tmp_path)
    manifest = make_manifest()
    path = store.save(manifest)
    assert path.is_file()
    assert not path.with_suffix(".json.tmp").exists()
    assert store.load("unit-job").status == JobStatus.CREATED


def test_state_transitions_are_checked(tmp_path: Path) -> None:
    store = ManifestStore(tmp_path)
    manifest = make_manifest()
    store.save(manifest)
    store.transition(manifest, JobStatus.SUBMITTED)
    store.transition(manifest, JobStatus.QUEUED)
    store.transition(manifest, JobStatus.RUNNING)
    store.transition(manifest, JobStatus.COMPLETED)
    assert manifest.finished_at is not None
    with pytest.raises(JobError):
        store.transition(manifest, JobStatus.RUNNING)
