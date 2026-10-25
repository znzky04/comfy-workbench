from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .client import ComfyClient
from .config import Settings
from .errors import JobError
from .manifests import ManifestStore
from .models import GenerationRequest, JobManifest, JobStatus
from .registry import WorkflowRegistry


def _input_record(path: Path) -> dict[str, str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path.resolve()), "sha256": digest}


class GenerationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.registry = WorkflowRegistry(settings.project_root)
        self.store = ManifestStore(settings.paths.manifest_root)

    def create_manifest(self, request: GenerationRequest, job_id: str | None = None) -> JobManifest:
        definition = self.registry.get(request.workflow_id)
        manifest = JobManifest(
            job_id=job_id or str(uuid.uuid4()),
            client=request.client,
            workflow_id=definition.workflow_id,
            workflow_version=definition.version,
            workflow_sha256=definition.sha256,
            request=request.model_dump(mode="json"),
            models=[*definition.requirements.models, *definition.requirements.upscalers],
            loras=definition.requirements.loras,
            input_images=[_input_record(path) for path in request.input_images],
        )
        self.store.save(manifest)
        return manifest

    def submit(self, request: GenerationRequest, wait: bool = False) -> JobManifest:
        manifest = self.create_manifest(request)
        try:
            with ComfyClient(self.settings) as client:
                client.health()
                uploaded = [client.upload_image(path) for path in request.input_images]
                resolved: list[dict] = []
                for index in range(request.count):
                    _, workflow, parameters = self.registry.prepare(
                        request, manifest.job_id, index, uploaded
                    )
                    remote_errors = client.validate_workflow(workflow)
                    if remote_errors:
                        raise JobError("；".join(remote_errors))
                    prompt_id = client.submit(workflow)
                    manifest.prompt_ids.append(prompt_id)
                    if manifest.prompt_id is None:
                        manifest.prompt_id = prompt_id
                    resolved.append(parameters)
                manifest.resolved_parameters = {"runs": resolved, "uploaded_images": uploaded}
                self.store.transition(manifest, JobStatus.SUBMITTED)
                self.store.transition(manifest, JobStatus.QUEUED)
                if wait:
                    return self.wait(manifest.job_id, client=client)
                return manifest
        except Exception as exc:
            manifest.error_category = type(exc).__name__
            manifest.error_detail = str(exc)
            if manifest.status not in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                self.store.transition(manifest, JobStatus.FAILED, str(exc))
            raise

    def wait(self, job_id: str, client: ComfyClient | None = None) -> JobManifest:
        manifest = self.store.load(job_id)
        if manifest.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return manifest
        owned_client = client is None
        client = client or ComfyClient(self.settings)
        try:
            self.store.transition(manifest, JobStatus.RUNNING)
            outputs: list[str] = []
            for prompt_id in manifest.prompt_ids:
                history = client.wait(prompt_id)
                outputs.extend(str(path) for path in client.output_paths(history))
                manifest.output_files = list(dict.fromkeys(outputs))
                self.store.save(manifest)
            manifest.output_files = list(dict.fromkeys(outputs))
            self.store.transition(manifest, JobStatus.COMPLETED)
            return manifest
        except Exception as exc:
            manifest.error_category = type(exc).__name__
            manifest.error_detail = str(exc)
            self.store.transition(manifest, JobStatus.FAILED, str(exc))
            raise
        finally:
            if owned_client:
                client.close()

    def cancel(self, job_id: str) -> JobManifest:
        manifest = self.store.load(job_id)
        if manifest.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return manifest
        with ComfyClient(self.settings) as client:
            for prompt_id in manifest.prompt_ids:
                client.cancel(prompt_id)
        self.store.transition(manifest, JobStatus.CANCELLED)
        return manifest

    def refresh(self, job_id: str) -> JobManifest:
        """Reconcile a persisted job with ComfyUI, including after a studio restart."""
        manifest = self.store.load(job_id)
        if manifest.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return manifest
        if not manifest.prompt_ids:
            return manifest
        with ComfyClient(self.settings) as client:
            histories = [client.history(prompt_id) for prompt_id in manifest.prompt_ids]
            available = list(
                dict.fromkeys(
                    str(path)
                    for history in histories
                    if history
                    for path in client.output_paths(history)
                )
            )
            if available != manifest.output_files:
                manifest.output_files = available
                self.store.save(manifest)
            for history in histories:
                if history and history.get("status", {}).get("status_str") == "error":
                    manifest.error_category = "ComfyExecutionError"
                    manifest.error_detail = str(history.get("status", {}))
                    return self.store.transition(manifest, JobStatus.FAILED, manifest.error_detail)
            if all(history and history.get("status", {}).get("completed") for history in histories):
                return self.store.transition(manifest, JobStatus.COMPLETED)
            queue = client.queue()
            running = {str(row[1]) for row in queue.get("queue_running", [])}
            if any(prompt_id in running for prompt_id in manifest.prompt_ids):
                self.store.transition(manifest, JobStatus.RUNNING)
            if (
                datetime.now(UTC) - manifest.created_at
            ).total_seconds() > self.settings.comfyui.job_timeout_seconds:
                manifest.error_category = "JobTimeout"
                manifest.error_detail = "任务观察超时；ComfyUI 端可能仍在运行，请查看其队列。"
                self.store.transition(manifest, JobStatus.FAILED, manifest.error_detail)
            return manifest
