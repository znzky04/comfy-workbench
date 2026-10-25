from __future__ import annotations

import hashlib
import mimetypes
import time
import uuid
from pathlib import Path
from typing import Any, Self

import httpx

from .config import Settings
from .errors import ComfyUnavailableError, JobError, WorkflowValidationError


class ComfyClient:
    """HTTP client for an externally managed ComfyUI instance."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = str(uuid.uuid4())
        self._http = httpx.Client(
            base_url=settings.comfyui.url,
            timeout=httpx.Timeout(settings.comfyui.connect_timeout_seconds),
            trust_env=False,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._http.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.NetworkError, httpx.TimeoutException) as exc:
            raise ComfyUnavailableError(
                f"无法连接 {self.settings.comfyui.url}。请手动打开 ComfyUI Desktop 后重试；本项目不会代为启动。"
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:1000]
            raise JobError(f"ComfyUI HTTP {exc.response.status_code}: {detail}") from exc

    def system_stats(self) -> dict[str, Any]:
        return self._request("GET", "/system_stats").json()

    def queue(self) -> dict[str, Any]:
        return self._request("GET", "/queue").json()

    def object_info(self) -> dict[str, Any]:
        return self._request("GET", "/object_info").json()

    def health(self) -> dict[str, Any]:
        started = time.perf_counter()
        stats = self.system_stats()
        return {
            "ok": True,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "system_stats": stats,
            "queue": self.queue(),
        }

    def validate_workflow(self, workflow: dict[str, Any]) -> list[str]:
        object_info = self.object_info()
        missing = sorted(
            {node.get("class_type", "") for node in workflow.values()} - set(object_info)
        )
        return [f"ComfyUI 未注册节点：{name}" for name in missing if name]

    def upload_image(self, path: Path) -> str:
        if not path.is_file():
            raise WorkflowValidationError(f"参考图不存在：{path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        upload_name = f"{digest}_{path.name}"
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as handle:
            response = self._request(
                "POST",
                "/upload/image",
                files={"image": (upload_name, handle, mime)},
                data={"type": "input", "subfolder": "comfyui-demo", "overwrite": "false"},
            )
        data = response.json()
        name = data.get("name", path.name)
        subfolder = data.get("subfolder", "comfyui-demo")
        return f"{subfolder}/{name}" if subfolder else name

    def upload_bytes(self, payload: bytes, filename: str, subfolder: str) -> str:
        """Let the owning ComfyUI process write to its configured input directory."""
        response = self._request(
            "POST",
            "/upload/image",
            files={"image": (filename, payload, mimetypes.guess_type(filename)[0])},
            data={"type": "input", "subfolder": subfolder, "overwrite": "false"},
        ).json()
        return f"{response.get('subfolder', subfolder)}/{response['name']}"

    def submit(self, workflow: dict[str, Any]) -> str:
        response = self._request(
            "POST", "/prompt", json={"prompt": workflow, "client_id": self.client_id}
        ).json()
        if response.get("node_errors"):
            raise WorkflowValidationError(str(response["node_errors"]))
        prompt_id = response.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise JobError(f"ComfyUI 未返回 prompt_id：{response}")
        return prompt_id

    def history(self, prompt_id: str) -> dict[str, Any] | None:
        data = self._request("GET", f"/history/{prompt_id}").json()
        item = data.get(prompt_id)
        return item if isinstance(item, dict) else None

    def wait(self, prompt_id: str, timeout_seconds: float | None = None) -> dict[str, Any]:
        timeout = timeout_seconds or self.settings.comfyui.job_timeout_seconds
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            item = self.history(prompt_id)
            if item is not None:
                status = item.get("status", {})
                if status.get("status_str") == "error" or status.get("completed") is False:
                    raise JobError(f"ComfyUI 任务失败：{status}")
                return item
            time.sleep(1)
        raise JobError(f"等待 ComfyUI 任务超时（{timeout:.0f}s）：{prompt_id}")

    def cancel(self, prompt_id: str) -> None:
        queue = self.queue()
        running = {str(item[1]) for item in queue.get("queue_running", []) if len(item) > 1}
        if prompt_id in running:
            self._request("POST", "/interrupt")
        else:
            self._request("POST", "/queue", json={"delete": [prompt_id]})

    def output_paths(self, history_item: dict[str, Any]) -> list[Path]:
        paths: list[Path] = []
        for output in history_item.get("outputs", {}).values():
            for kind in ("images", "gifs", "audio"):
                for artifact in output.get(kind, []):
                    filename = artifact.get("filename")
                    if not filename:
                        continue
                    subfolder = artifact.get("subfolder", "")
                    artifact_type = artifact.get("type", "output")
                    if artifact_type == "output":
                        root = self.settings.paths.canonical_output_root.parent
                    elif artifact_type == "input":
                        root = self.settings.paths.canonical_input_root
                    else:
                        root = self.settings.paths.workspace / artifact_type
                    paths.append((root / subfolder / filename).resolve())
        return paths

    def installed_dependencies(self, names: list[str]) -> dict[str, bool]:
        model_roots = self.settings.paths.model_roots or [self.settings.paths.workspace / "models"]
        wanted = set(names)
        found: set[str] = set()
        for model_root in model_roots:
            if not model_root.is_dir():
                continue
            for path in model_root.rglob("*"):
                if path.is_file() and path.name in wanted:
                    found.add(path.name)
                    if found == wanted:
                        break
            if found == wanted:
                break
        return {name: name in found for name in names}
