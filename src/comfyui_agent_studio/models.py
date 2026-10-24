from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ClientName = Literal["cli", "inbox", "studio", "codex", "dsh"]


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    prompt: str = Field(min_length=1)
    negative_prompt: str | None = None
    seed: int | None = Field(default=None, ge=-1, le=18446744073709551615)
    count: int = Field(default=1, ge=1, le=4)
    width: int | None = Field(default=None, ge=256, le=2048)
    height: int | None = Field(default=None, ge=256, le=2048)
    steps: int | None = Field(default=None, ge=1, le=100)
    cfg: float | None = Field(default=None, ge=0, le=30)
    denoise: float | None = Field(default=None, ge=0, le=1)
    input_images: list[Path] = Field(default_factory=list, max_length=4)
    output_label: str | None = Field(default=None, max_length=80, pattern=r"^[\w\-. ]+$")
    client: ClientName = "cli"

    @field_validator("prompt")
    @classmethod
    def prompt_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("prompt must not be blank")
        return value

    @field_validator("width", "height")
    @classmethod
    def dimension_multiple_of_eight(cls, value: int | None) -> int | None:
        if value is not None and value % 8:
            raise ValueError("dimensions must be multiples of 8")
        return value


class JobStatus(StrEnum):
    CREATED = "created"
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StateEvent(BaseModel):
    status: JobStatus
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail: str | None = None


class JobManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    job_id: str
    prompt_id: str | None = None
    prompt_ids: list[str] = Field(default_factory=list)
    client: ClientName
    workflow_id: str
    workflow_version: str
    workflow_sha256: str
    request: dict
    resolved_parameters: dict = Field(default_factory=dict)
    models: list[str] = Field(default_factory=list)
    loras: list[str] = Field(default_factory=list)
    input_images: list[dict] = Field(default_factory=list)
    status: JobStatus = JobStatus.CREATED
    state_history: list[StateEvent] = Field(
        default_factory=lambda: [StateEvent(status=JobStatus.CREATED)]
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output_files: list[str] = Field(default_factory=list)
    error_category: str | None = None
    error_detail: str | None = None
