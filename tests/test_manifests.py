from pathlib import Path

import pytest

from comfyui_agent_studio.errors import JobError
from comfyui_agent_studio.manifests import ManifestStore
from comfyui_agent_studio.models import HumanEvaluation, JobManifest, JobStatus


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


def test_manifest_keeps_benchmark_evaluation(tmp_path: Path) -> None:
    store = ManifestStore(tmp_path)
    manifest = make_manifest()
    manifest.benchmark_task_id = "steampunk-engineer"
    manifest.human_evaluation = HumanEvaluation(
        identity_or_signature_features_1_to_5=5,
        composition_1_to_5=4,
        anatomy_1_to_5=4,
        material_and_detail_1_to_5=5,
        overall_1_to_5=4,
        notes="test",
    )
    store.save(manifest)
    loaded = store.load(manifest.job_id)
    assert loaded.benchmark_task_id == "steampunk-engineer"
    assert loaded.human_evaluation is not None
    assert loaded.human_evaluation.overall_1_to_5 == 4


@pytest.mark.parametrize("job_id", ["../escape", "*", "one/two", "C:\\outside", ""])
def test_manifest_rejects_path_or_glob_as_job_id(tmp_path, job_id):
    store = ManifestStore(tmp_path)
    with pytest.raises(JobError, match="非法任务 ID"):
        store.path_for(job_id)
    assert list(tmp_path.iterdir()) == []
