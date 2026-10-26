from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .errors import JobError
from .models import JobManifest, JobStatus, StateEvent

ALLOWED_TRANSITIONS = {
    JobStatus.CREATED: {JobStatus.SUBMITTED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.SUBMITTED: {
        JobStatus.QUEUED,
        JobStatus.RUNNING,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.QUEUED: {
        JobStatus.RUNNING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    },
    JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


class ManifestStore:
    def __init__(self, root: Path):
        self.root = root

    def path_for(self, job_id: str, created_at: datetime | None = None) -> Path:
        if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", job_id) is None:
            raise JobError("非法任务 ID")
        if created_at is None:
            matches = list(self.root.glob(f"*/*/{job_id}.json"))
            if matches:
                return matches[0]
            created_at = datetime.now(UTC)
        return self.root / f"{created_at:%Y}" / f"{created_at:%m}" / f"{job_id}.json"

    def save(self, manifest: JobManifest) -> Path:
        path = self.path_for(manifest.job_id, manifest.created_at)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = manifest.model_dump_json(indent=2)
        # Unique names avoid collisions between concurrent writers of the same job.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{manifest.job_id}.",
            suffix=".tmp", delete=False,
        ) as handle:
            temp = Path(handle.name)
            try:
                handle.write(payload + "\n")
            except BaseException:
                handle.close()
                temp.unlink(missing_ok=True)
                raise
        try:
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return path

    def load(self, job_id: str) -> JobManifest:
        path = self.path_for(job_id)
        if not path.is_file():
            raise JobError(f"任务记录不存在：{job_id}")
        return JobManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def transition(
        self, manifest: JobManifest, status: JobStatus, detail: str | None = None
    ) -> JobManifest:
        if status == manifest.status:
            return manifest
        if status not in ALLOWED_TRANSITIONS[manifest.status]:
            raise JobError(f"非法任务状态转换：{manifest.status} → {status}")
        manifest.status = status
        manifest.state_history.append(StateEvent(status=status, detail=detail))
        now = datetime.now(UTC)
        if status == JobStatus.RUNNING and manifest.started_at is None:
            manifest.started_at = now
        if status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            manifest.finished_at = now
        self.save(manifest)
        return manifest

    def list_recent(self, limit: int = 50) -> list[JobManifest]:
        files = sorted(self.root.glob("*/*/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        manifests: list[JobManifest] = []
        for path in files[:limit]:
            try:
                manifests.append(JobManifest.model_validate_json(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return manifests
