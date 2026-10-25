from __future__ import annotations

import asyncio
import hashlib
import io
import json
import secrets
import tempfile
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .client import ComfyClient
from .config import Settings, load_settings
from .errors import JobError, StudioError, WorkflowValidationError
from .models import GenerationRequest, JobStatus
from .service import GenerationService

ASSETS = Path(__file__).parent / "web_assets"
TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    service = GenerationService(settings)
    # Multipart spooling stays on the project drive, including uploads over 1 MB.
    spool_root = settings.paths.manifest_root / "web-temp"
    spool_root.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(spool_root)
    token = secrets.token_urlsafe(32)
    locks: dict[str, asyncio.Lock] = {}
    uploads = settings.paths.canonical_input_root / "comfyui-demo" / "studio"
    templates = Jinja2Templates(directory=str(ASSETS))

    async def reconcile(job_id: str):
        async with locks.setdefault(job_id, asyncio.Lock()):
            return await run_in_threadpool(service.refresh, job_id)

    async def monitor():
        while True:
            for job in await run_in_threadpool(service.store.list_recent, 500):
                if job.status not in TERMINAL and job.prompt_ids:
                    try:
                        await reconcile(job.job_id)
                    except StudioError:
                        # A temporarily closed Desktop must not destroy resumable state.
                        pass
            await asyncio.sleep(2)

    @asynccontextmanager
    async def lifespan(app):
        worker = asyncio.create_task(monitor())
        yield
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass

    app = FastAPI(title="ComfyUI Agent Studio", lifespan=lifespan)
    app.state.service = service
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.middleware("http")
    async def upload_request_limit(request: Request, call_next):
        if request.method == "POST" and request.url.path == "/api/uploads":
            maximum = settings.web.upload_max_mb * 1024 * 1024 + 65536
            length = request.headers.get("content-length")
            if length is not None and (not length.isdecimal() or int(length) > maximum):
                return JSONResponse({"detail": "上传请求超过大小限制"}, status_code=413)
            received = 0
            original_receive = request._receive

            async def limited_receive():
                nonlocal received
                message = await original_receive()
                received += len(message.get("body", b""))
                if received > maximum:
                    raise HTTPException(413, "上传请求超过大小限制")
                return message

            request._receive = limited_receive
        response = await call_next(request)
        if request.method == "POST" and request.url.path == "/api/uploads" and received > maximum:
            # Multipart parsing wraps receive errors as 400; retain the size-limit status.
            return JSONResponse({"detail": "上传请求超过大小限制"}, status_code=413)
        return response

    app.mount("/static", StaticFiles(directory=str(ASSETS)), name="static")

    @app.exception_handler(StudioError)
    async def studio_error(request, exc):
        status = 422 if isinstance(exc, WorkflowValidationError) else 503
        if isinstance(exc, JobError) and "任务记录不存在" in str(exc):
            status = 404
        return JSONResponse({"detail": str(exc)}, status_code=status)

    def protect(request: Request):
        if not secrets.compare_digest(request.headers.get("x-studio-token", ""), token):
            raise HTTPException(403, "请刷新本地工作台后重试。")

    def load_job(job_id: str):
        if not job_id or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in job_id
        ):
            raise HTTPException(404, "任务不存在")
        return service.store.load(job_id)

    def present(job):
        value = job.model_dump(mode="json")
        value["artifacts"] = [
            {"id": index, "path": filename, "url": f"/api/artifacts/{job.job_id}/{index}"}
            for index, filename in enumerate(job.output_files)
        ]
        value["phase"] = job.status
        return value

    @app.get("/")
    async def index(request: Request):
        return templates.TemplateResponse(
            request=request, name="index.html", context={"token": token}
        )

    @app.get("/api/health")
    async def health():
        def snapshot():
            try:
                with ComfyClient(settings) as client:
                    return {
                        "connected": True,
                        "system": client.system_stats(),
                        "queue": client.queue(),
                    }
            except StudioError as exc:
                return {"connected": False, "error": str(exc)}

        return await run_in_threadpool(snapshot)

    @app.get("/api/workflows")
    async def workflows():
        return [item.model_dump() for item in service.registry.list()]

    @app.get("/api/workflows/{workflow_id}")
    async def workflow(workflow_id: str):
        definition = service.registry.get(workflow_id)
        graph = service.registry.load_workflow(definition)
        value = definition.model_dump()
        value["defaults"] = {
            key: graph[binding.node_id]["inputs"][binding.input]
            for key, binding in definition.parameters.items()
        }
        return value

    @app.post("/api/uploads", dependencies=[Depends(protect)])
    async def upload(file: Annotated[UploadFile, File()]):
        maximum = settings.web.upload_max_mb * 1024 * 1024
        payload = bytearray()
        while chunk := await file.read(1024 * 1024):
            payload.extend(chunk)
            if len(payload) > maximum:
                raise HTTPException(413, f"参考图不得超过 {settings.web.upload_max_mb} MB")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(payload)) as picture:
                    format_name = picture.format
                    width, height = picture.size
                    if format_name not in {"PNG", "JPEG", "WEBP"} or width * height > 40_000_000:
                        raise ValueError("参考图需为 PNG、JPEG 或 WebP，且不超过 4000 万像素")
                    picture.verify()
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombWarning,
            Image.DecompressionBombError,
        ) as exc:
            raise HTTPException(422, "无法读取参考图；请使用有效 PNG/JPEG/WebP。") from exc
        digest = hashlib.sha256(payload).hexdigest()
        extension = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[format_name]

        def send_input():
            with ComfyClient(settings) as client:
                return client.upload_bytes(
                    bytes(payload), digest + extension, "comfyui-demo/studio"
                )

        uploaded = await run_in_threadpool(send_input)
        path = settings.paths.canonical_input_root / uploaded
        if not path.resolve().is_relative_to(uploads.resolve()):
            raise HTTPException(502, "ComfyUI 返回了不符合输入目录约定的路径")
        return {"path": str(path), "sha256": digest, "width": width, "height": height}

    @app.post("/api/jobs", dependencies=[Depends(protect)], status_code=202)
    async def submit(request: GenerationRequest):
        for path in request.input_images:
            if not path.resolve().is_relative_to(uploads.resolve()) or not path.is_file():
                raise HTTPException(422, "请先通过工作台上传参考图。")
        request = request.model_copy(update={"client": "studio"})
        # Validate before writing a job or touching the remote queue.
        service.registry.prepare(
            request, "preflight", 0, ["preflight.png"] if request.input_images else []
        )
        submitted = await run_in_threadpool(service.submit, request, False)
        return present(submitted)

    @app.get("/api/jobs")
    async def jobs(limit: int = 100):
        return [
            present(job)
            for job in await run_in_threadpool(service.store.list_recent, min(max(limit, 1), 500))
        ]

    @app.get("/api/jobs/{job_id}")
    async def job(job_id: str):
        return present(load_job(job_id))

    @app.get("/api/jobs/{job_id}/events")
    async def events(job_id: str, request: Request):
        load_job(job_id)

        async def stream():
            previous = None
            while not await request.is_disconnected():
                current = load_job(job_id)
                encoded = json.dumps(present(current), ensure_ascii=False)
                if encoded != previous:
                    yield f"event: job\ndata: {encoded}\n\n"
                    previous = encoded
                else:
                    yield ": heartbeat\n\n"
                if current.status in TERMINAL:
                    break
                await asyncio.sleep(1)

        return StreamingResponse(
            stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    @app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(protect)])
    async def cancel(job_id: str):
        load_job(job_id)
        async with locks.setdefault(job_id, asyncio.Lock()):
            result = await run_in_threadpool(service.cancel, job_id)
        return present(result)

    @app.get("/api/artifacts/{job_id}/{artifact_id}")
    async def artifact(job_id: str, artifact_id: int):
        job = load_job(job_id)
        if artifact_id < 0 or artifact_id >= len(job.output_files):
            raise HTTPException(404, "图片不存在")
        path = Path(job.output_files[artifact_id]).resolve()
        # Includes retained legacy DSH outputs, but never arbitrary manifest paths.
        if not path.is_relative_to(settings.paths.canonical_output_root.parent.resolve()):
            raise HTTPException(403, "图片不在权威图库中")
        if not path.is_file():
            raise HTTPException(404, "图库文件不存在；运行记录仍保留")
        return FileResponse(path, headers={"X-Content-Type-Options": "nosniff"})

    @app.get("/api/benchmarks")
    async def benchmarks():
        return json.loads(
            (settings.project_root / "benchmarks/characters.json").read_text(encoding="utf-8")
        )

    return app
