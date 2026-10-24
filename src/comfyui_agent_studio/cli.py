from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .config import load_settings
from .diagnostics import doctor as run_doctor
from .dsh import build_bundle, verify_bundle
from .errors import StudioError
from .inbox import InboxWatcher
from .models import GenerationRequest
from .registry import WorkflowRegistry
from .service import GenerationService

app = typer.Typer(help="ComfyUI Agent Studio：连接用户手动管理的 ComfyUI Desktop。")
workflow_app = typer.Typer(help="查看和校验版本化工作流。")
job_app = typer.Typer(help="查看、等待和取消任务。")
dsh_app = typer.Typer(help="构建和校验 DSH preset v1 包。")
showcase_app = typer.Typer(help="人工批准的公开样例导出。")
app.add_typer(workflow_app, name="workflow")
app.add_typer(job_app, name="job")
app.add_typer(dsh_app, name="dsh")
app.add_typer(showcase_app, name="showcase")


def _echo_json(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _handle(callable_):
    try:
        return callable_()
    except StudioError as exc:
        typer.echo(f"错误：{exc}", err=True)
        raise typer.Exit(1) from exc


@app.command()
def doctor(remote: Annotated[bool, typer.Option(help="检查 ComfyUI、模型和节点。")] = True) -> None:
    """检查连接、磁盘、队列、工作流、模型和自定义节点。"""
    settings = load_settings()
    _echo_json(run_doctor(settings, remote=remote))


@workflow_app.command("list")
def workflow_list() -> None:
    registry = WorkflowRegistry()
    _echo_json(
        [
            {
                "workflow_id": item.workflow_id,
                "version": item.version,
                "mode": item.mode,
                "sha256": item.sha256,
            }
            for item in registry.list()
        ]
    )


@workflow_app.command("show")
def workflow_show(workflow_id: str) -> None:
    registry = WorkflowRegistry()
    _echo_json(registry.get(workflow_id).model_dump())


@workflow_app.command("validate")
def workflow_validate(
    workflow_id: str | None = typer.Argument(None),
    all_workflows: Annotated[bool, typer.Option("--all", help="校验全部工作流。")] = False,
    remote: Annotated[bool, typer.Option(help="同时连接 ComfyUI 校验节点。")] = False,
) -> None:
    def action() -> None:
        registry = WorkflowRegistry()
        if all_workflows:
            result = registry.validate_all()
        elif workflow_id:
            result = {workflow_id: registry.validate(workflow_id)}
        else:
            raise typer.BadParameter("请提供 workflow_id 或 --all")
        payload: dict = {"static": result}
        if remote:
            payload["doctor"] = run_doctor(load_settings(), remote=True)["remote"]
        _echo_json(payload)
        if any(result.values()):
            raise typer.Exit(1)

    _handle(action)


@app.command()
def run(
    workflow_id: str,
    prompt: Annotated[str, typer.Option("--prompt", "-p")],
    negative_prompt: Annotated[str | None, typer.Option("--negative-prompt")] = None,
    seed: int | None = None,
    count: int = 1,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    denoise: float | None = None,
    input_image: Annotated[list[Path] | None, typer.Option("--input-image")] = None,
    wait: bool = True,
) -> None:
    def action() -> None:
        request = GenerationRequest(
            workflow_id=workflow_id,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            count=count,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            denoise=denoise,
            input_images=input_image or [],
            client="cli",
        )
        manifest = GenerationService(load_settings()).submit(request, wait=wait)
        _echo_json(manifest.model_dump(mode="json"))

    _handle(action)


@job_app.command("show")
def job_show(job_id: str) -> None:
    service = GenerationService(load_settings())
    _echo_json(service.store.load(job_id).model_dump(mode="json"))


@job_app.command("wait")
def job_wait(job_id: str) -> None:
    _handle(
        lambda: _echo_json(GenerationService(load_settings()).wait(job_id).model_dump(mode="json"))
    )


@job_app.command("cancel")
def job_cancel(job_id: str) -> None:
    _handle(
        lambda: _echo_json(
            GenerationService(load_settings()).cancel(job_id).model_dump(mode="json")
        )
    )


@app.command()
def watch(once: bool = False, interval: float = 2) -> None:
    watcher = InboxWatcher(GenerationService(load_settings()))
    if once:
        _echo_json(watcher.scan())
    else:
        typer.echo(f"监听：{watcher.root / 'pending'}（Ctrl+C 停止）")
        watcher.watch(interval)


@app.command()
def studio() -> None:
    """M5 通过前保持锁定，避免网页形成第二套未验证实现。"""
    typer.echo("本地网页受阶段门禁保护：完成 M5 的 8 个真实任务后才启用 M6。")
    raise typer.Exit(2)


@dsh_app.command("bundle")
def dsh_bundle(version: str = "0.1.0", output: Path | None = None) -> None:
    _handle(lambda: _echo_json(verify_bundle(build_bundle(output=output, version=version))))


@dsh_app.command("verify")
def dsh_verify(path: Path) -> None:
    _handle(lambda: _echo_json(verify_bundle(path)))


@showcase_app.command("export")
def showcase_export(selection_file: Path) -> None:
    typer.echo(
        f"公开导出受 M5/M6 门禁保护。已读取选择文件参数：{selection_file}；当前不会复制任何图片。"
    )
    raise typer.Exit(2)


if __name__ == "__main__":
    app()
