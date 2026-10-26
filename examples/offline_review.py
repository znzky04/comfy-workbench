"""Exercise core contracts without ComfyUI, models, network or generated images."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from comfyui_agent_studio.manifests import ManifestStore
from comfyui_agent_studio.models import GenerationRequest, JobManifest, JobStatus
from comfyui_agent_studio.registry import WorkflowRegistry


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    scratch = root / "runs" / "offline-review"
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="contract-", dir=scratch) as directory:
        sample = Path(directory)
        api_path = sample / "workflows" / "example.json"
        api_path.parent.mkdir()
        # This minimal graph demonstrates bindings only; it is never submitted.
        graph = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "example"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": 1}},
            "3": {"class_type": "SaveImage", "inputs": {"filename_prefix": "example"}},
        }
        api_path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        digest = hashlib.sha256(api_path.read_bytes()).hexdigest()
        definition = {
            "workflow_id": "review.example.v1",
            "version": "1.0.0",
            "title": "Offline contract fixture, not a runnable generation graph",
            "mode": "txt2img",
            "api_path": "workflows/example.json",
            "sha256": digest,
            "parameters": {
                "prompt": {"node_id": "1", "input": "text", "type": "string"},
                "seed": {"node_id": "2", "input": "seed", "type": "integer"},
            },
            "requirements": {},
            "output_nodes": ["3"],
            "save_node": "3",
            "dsh": {"tags": ["offline-example"], "skill_path": "unused"},
        }
        (sample / "workflows" / "registry.json").write_text(
            json.dumps({"schema_version": 1, "workflows": [definition]}), encoding="utf-8"
        )
        registry = WorkflowRegistry(sample)
        request = GenerationRequest(
            workflow_id="review.example.v1", prompt="offline review example", seed=0
        )
        _, prepared, resolved = registry.prepare(request, "review-job", 0)
        assert prepared["2"]["inputs"]["seed"] == 0
        assert resolved["output_prefix"].endswith("review-job_0_1")
        print("PASS: validated parameter binding, seed 0 and output naming")

        store = ManifestStore(sample / "runs")
        manifest = JobManifest(
            job_id="review-job", client="cli", workflow_id=definition["workflow_id"],
            workflow_version=definition["version"], workflow_sha256=digest,
            request=request.model_dump(mode="json"),
        )
        manifest.prompt_ids = ["offline-placeholder-not-a-remote-task"]
        store.save(manifest)
        store.transition(manifest, JobStatus.SUBMITTED)
        store.transition(manifest, JobStatus.QUEUED)
        restored = ManifestStore(sample / "runs").load("review-job")
        assert restored.prompt_ids == manifest.prompt_ids
        assert restored.status == JobStatus.QUEUED
        print("PASS: a new store reloads the persisted task identity and state")

        api_path.write_text(api_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        assert any("SHA-256" in error for error in registry.validate(request.workflow_id))
        print("PASS: workflow content drift is detected")
    print("Finished offline. No backend requests, generation or original workflow changes.")


if __name__ == "__main__":
    main()
