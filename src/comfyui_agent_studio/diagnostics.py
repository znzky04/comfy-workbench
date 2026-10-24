from __future__ import annotations

import shutil
import socket
from typing import Any
from urllib.parse import urlparse

from .client import ComfyClient
from .config import Settings
from .errors import StudioError
from .registry import WorkflowRegistry


def _port_open(url: str, timeout: float) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def doctor(settings: Settings, remote: bool = True) -> dict[str, Any]:
    registry = WorkflowRegistry(settings.project_root)
    static = registry.validate_all()
    disk_probe = settings.paths.canonical_output_root
    while not disk_probe.exists() and disk_probe != disk_probe.parent:
        disk_probe = disk_probe.parent
    free = shutil.disk_usage(disk_probe)
    port_open = _port_open(settings.comfyui.url, min(settings.comfyui.connect_timeout_seconds, 1))
    report: dict[str, Any] = {
        "lifecycle": settings.comfyui.lifecycle,
        "comfyui_url": settings.comfyui.url,
        "port_open": port_open,
        "workspace_exists": settings.paths.workspace.is_dir(),
        "output_root": str(settings.paths.canonical_output_root),
        "output_parent_exists": settings.paths.canonical_output_root.parent.is_dir(),
        "free_gb": round(free.free / 1024**3, 2),
        "disk_warning": free.free / 1024**3 < settings.retention.disk_warning_free_gb,
        "workflow_validation": static,
        "remote": None,
    }
    if not remote:
        return report
    if not port_open:
        report["remote"] = {
            "connected": False,
            "error": (
                f"无法连接 {settings.comfyui.url}。请手动打开 ComfyUI Desktop 后重试；"
                "本项目不会代为启动。"
            ),
        }
        return report
    try:
        with ComfyClient(settings) as client:
            health = client.health()
            classes = client.object_info()
            definitions = registry.list()
            dependency_names = sorted(
                {
                    name
                    for definition in definitions
                    for name in (
                        definition.requirements.models
                        + definition.requirements.loras
                        + definition.requirements.upscalers
                    )
                }
            )
            custom_nodes = sorted(
                {
                    name
                    for definition in definitions
                    for name in definition.requirements.custom_nodes
                }
            )
            report["remote"] = {
                "connected": True,
                "health": health,
                "dependencies": client.installed_dependencies(dependency_names),
                "custom_nodes": {name: name in classes for name in custom_nodes},
            }
    except StudioError as exc:
        report["remote"] = {"connected": False, "error": str(exc)}
    return report
