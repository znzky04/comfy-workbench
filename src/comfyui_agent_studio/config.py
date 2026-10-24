from __future__ import annotations

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ComfyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = "http://127.0.0.1:8188"
    lifecycle: str = "external"
    connect_timeout_seconds: float = Field(default=5, gt=0, le=60)
    job_timeout_seconds: float = Field(default=900, gt=0)

    @field_validator("url")
    @classmethod
    def strip_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("lifecycle")
    @classmethod
    def external_only(cls, value: str) -> str:
        if value != "external":
            raise ValueError("ComfyUI lifecycle must remain 'external'")
        return value


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace: Path
    workflow_root: Path = Path("workflows/api")
    manifest_root: Path = Path("runs")
    canonical_output_root: Path


class RetentionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delete_generated_images: bool = False
    log_max_mb: int = Field(default=5, ge=1, le=100)
    log_backup_count: int = Field(default=5, ge=1, le=20)
    disk_warning_free_gb: float = Field(default=50, ge=0)

    @field_validator("delete_generated_images")
    @classmethod
    def never_delete(cls, value: bool) -> bool:
        if value:
            raise ValueError("automatic image deletion is forbidden")
        return value


class WebConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "127.0.0.1"
    port: int = Field(default=8199, ge=1024, le=65535)
    upload_max_mb: int = Field(default=25, ge=1, le=256)

    @field_validator("host")
    @classmethod
    def loopback_only(cls, value: str) -> str:
        if value not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("the local studio may only listen on loopback")
        return value


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_root: Path = PROJECT_ROOT
    comfyui: ComfyConfig
    paths: PathsConfig
    retention: RetentionConfig
    web: WebConfig

    @model_validator(mode="after")
    def resolve_paths(self) -> Settings:
        for field_name in ("workflow_root", "manifest_root"):
            value = getattr(self.paths, field_name)
            if not value.is_absolute():
                setattr(self.paths, field_name, (self.project_root / value).resolve())
        self.paths.workspace = self.paths.workspace.resolve()
        self.paths.canonical_output_root = self.paths.canonical_output_root.resolve()
        return self


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"配置文件不存在：{path}") from exc


def load_settings(config_path: Path | None = None) -> Settings:
    example = PROJECT_ROOT / "config.example.toml"
    raw = _read_toml(example)
    local = config_path or (PROJECT_ROOT / "config.local.toml")
    if local.exists():
        raw = _merge(raw, _read_toml(local))

    env_map = {
        "COMFY_DEMO_COMFYUI_URL": ("comfyui", "url"),
        "COMFY_DEMO_WORKSPACE": ("paths", "workspace"),
        "COMFY_DEMO_OUTPUT_ROOT": ("paths", "canonical_output_root"),
        "COMFY_DEMO_WEB_HOST": ("web", "host"),
        "COMFY_DEMO_WEB_PORT": ("web", "port"),
    }
    for env_name, (section, key) in env_map.items():
        value = os.environ.get(env_name)
        if value is None:
            continue
        raw.setdefault(section, {})[key] = int(value) if key == "port" else value

    try:
        return Settings(project_root=PROJECT_ROOT, **raw)
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc
