import io
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.errors import ComfyUnavailableError
from comfyui_agent_studio.models import GenerationRequest, JobStatus
from comfyui_agent_studio.web import create_app


@pytest.fixture
def studio(tmp_path, monkeypatch):
    settings = load_settings()
    settings.paths.manifest_root = tmp_path / "runs"
    settings.paths.canonical_input_root = tmp_path / "input"
    settings.paths.canonical_output_root = tmp_path / "output/comfyui-demo"
    settings.web.upload_max_mb = 1

    def upload_bytes(self, payload, filename, subfolder):
        path = self.settings.paths.canonical_input_root / subfolder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return f"{subfolder}/{filename}"

    monkeypatch.setattr("comfyui_agent_studio.web.ComfyClient.upload_bytes", upload_bytes)
    app = create_app(settings)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        token = re.search(r'name="studio-token" content="([^"]+)"', client.get("/").text)[1]
        yield client, app.state.service, {"x-studio-token": token}


def image_bytes():
    data = io.BytesIO()
    Image.new("RGB", (16, 24), "navy").save(data, format="PNG")
    return data.getvalue()


def test_web_schema_csrf_and_host(studio):
    client, _, headers = studio
    assert "<title>星夜绘图室 · Comfy Workbench</title>" in client.get("/").text
    assert len(client.get("/api/workflows").json()) == 5
    assert client.get("/api/workflows/anima.standard.v1").json()["defaults"]["width"] > 0
    assert client.post("/api/jobs", json={}).status_code == 403
    assert client.get("/", headers={"host": "evil.example"}).status_code == 400
    response = client.post(
        "/api/jobs",
        headers=headers,
        json={
            "workflow_id": "anima.standard.v1",
            "prompt": "test",
            "unknown": 1,
        },
    )
    assert response.status_code == 422


def test_upload_content_limit_and_reference_boundary(studio):
    client, service, headers = studio
    bad = client.post(
        "/api/uploads", headers=headers, files={"file": ("fake.png", b"not a picture")}
    )
    assert bad.status_code == 422
    large = client.post(
        "/api/uploads", headers=headers, files={"file": ("x.png", b"x" * 1_048_577)}
    )
    assert large.status_code == 413
    payload = image_bytes()
    a = client.post(
        "/api/uploads", headers=headers, files={"file": ("../../bad.png", payload)}
    ).json()
    b = client.post("/api/uploads", headers=headers, files={"file": ("other.png", payload)}).json()
    assert a["path"] == b["path"]
    assert Path(a["path"]).read_bytes() == payload
    response = client.post(
        "/api/jobs",
        headers=headers,
        json={
            "workflow_id": "larkie.img2img.v1",
            "prompt": "test",
            "input_images": [str(service.settings.project_root / "README.md")],
        },
    )
    assert response.status_code == 422


def test_history_sse_artifact_and_cancel_terminal(studio):
    client, service, headers = studio
    manifest = service.create_manifest(
        GenerationRequest(
            workflow_id="anima.standard.v1",
            prompt="original character",
            client="studio",
            seed=0,
        )
    )
    image = service.settings.paths.canonical_output_root / "test.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(image_bytes())
    manifest.output_files = [str(image)]
    service.store.transition(manifest, JobStatus.SUBMITTED)
    service.store.transition(manifest, JobStatus.QUEUED)
    service.store.transition(manifest, JobStatus.COMPLETED)
    assert client.get("/api/jobs").json()[0]["artifacts"][0]["path"] == str(image)
    event = client.get(f"/api/jobs/{manifest.job_id}/events")
    assert "event: job" in event.text and '"completed"' in event.text
    url = f"/api/artifacts/{manifest.job_id}/0"
    assert client.get(url).content == image.read_bytes()
    assert client.get(f"/api/artifacts/{manifest.job_id}/-1").status_code == 404
    cancelled = client.post(f"/api/jobs/{manifest.job_id}/cancel", headers=headers)
    assert cancelled.json()["status"] == "completed"
    manifest.output_files = [str(service.settings.project_root / "README.md")]
    service.store.save(manifest)
    assert client.get(url).status_code == 403
    assert client.get("/api/jobs/not-found").status_code == 404


def test_submit_and_reconcile_share_core(studio, monkeypatch):
    client, service, headers = studio

    class Backend:
        complete = False

        def __init__(self, settings):
            self.settings = settings

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def health(self):
            return {"ok": True}

        def validate_workflow(self, workflow):
            return []

        def submit(self, workflow):
            assert workflow["40"]["inputs"]["seed"] == 0
            return "web-contract-prompt"

        def queue(self):
            return {"queue_running": [[0, "web-contract-prompt"]]}

        def history(self, prompt_id):
            return {"status": {"completed": True}, "outputs": {}} if self.complete else None

        def output_paths(self, history):
            return []

    monkeypatch.setattr("comfyui_agent_studio.service.ComfyClient", Backend)
    result = client.post(
        "/api/jobs",
        headers=headers,
        json={
            "workflow_id": "anima.standard.v1",
            "prompt": "test",
            "seed": 0,
            "client": "dsh",
        },
    )
    assert result.status_code == 202, result.text
    job_id = result.json()["job_id"]
    assert result.json()["client"] == "studio"
    assert service.refresh(job_id).status == "running"
    Backend.complete = True
    assert service.refresh(job_id).status == "completed"


def test_offline_health_is_actionable(studio, monkeypatch):
    client, _, _ = studio

    def unavailable(self):
        raise ComfyUnavailableError("请手动打开 ComfyUI Desktop")

    monkeypatch.setattr("comfyui_agent_studio.web.ComfyClient.system_stats", unavailable)
    health = client.get("/api/health").json()
    assert not health["connected"]
    assert "手动打开" in health["error"]


def test_chunked_upload_is_size_limited(studio):
    client, _, headers = studio
    response = client.post(
        "/api/uploads",
        headers={
            **headers,
            "content-type": "multipart/form-data; boundary=testboundary",
        },
        content=iter(
            [
                b'--testboundary\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n\r\n',
                b"x" * (1_048_576 + 65537),
                b"\r\n--testboundary--\r\n",
            ]
        ),
    )
    assert response.status_code == 413
