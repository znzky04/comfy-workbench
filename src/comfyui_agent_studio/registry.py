from __future__ import annotations

import hashlib
import json
import secrets
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .config import PROJECT_ROOT
from .errors import WorkflowValidationError
from .models import GenerationRequest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MirrorBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    input: str


class ParameterBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    input: str
    type: Literal["string", "integer", "number", "image"]
    required: bool = False
    minimum: float | None = None
    maximum: float | None = None
    multiple_of: int | None = None
    mirrors: list[MirrorBinding] = Field(default_factory=list)


class Requirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    models: list[str] = Field(default_factory=list)
    loras: list[str] = Field(default_factory=list)
    upscalers: list[str] = Field(default_factory=list)
    custom_nodes: list[str] = Field(default_factory=list)


class DshMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[str]
    skill_path: str
    require_skill: bool = False


class WorkflowDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    version: str
    title: str
    mode: Literal["txt2img", "img2img", "incontext", "upscale"]
    api_path: str
    sha256: str
    source_canvas: str | None = None
    parameters: dict[str, ParameterBinding]
    requirements: Requirements
    output_nodes: list[str]
    save_node: str
    dsh: DshMetadata


class RegistryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    workflows: list[WorkflowDefinition]


class WorkflowRegistry:
    def __init__(self, root: Path = PROJECT_ROOT, registry_path: Path | None = None):
        self.root = root
        self.registry_path = registry_path or (root / "workflows" / "registry.json")
        raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
        document = RegistryDocument.model_validate(raw)
        self._items = {item.workflow_id: item for item in document.workflows}
        if len(self._items) != len(document.workflows):
            raise WorkflowValidationError("工作流注册表包含重复 workflow_id")

    def list(self) -> list[WorkflowDefinition]:
        return list(self._items.values())

    def get(self, workflow_id: str) -> WorkflowDefinition:
        try:
            return self._items[workflow_id]
        except KeyError as exc:
            raise WorkflowValidationError(f"未注册的工作流：{workflow_id}") from exc

    def path_for(self, definition: WorkflowDefinition) -> Path:
        return (self.root / definition.api_path).resolve()

    def load_workflow(self, definition: WorkflowDefinition) -> dict[str, Any]:
        return json.loads(self.path_for(definition).read_text(encoding="utf-8"))

    def validate(self, workflow_id: str) -> list[str]:
        definition = self.get(workflow_id)
        path = self.path_for(definition)
        errors: list[str] = []
        if not path.is_file():
            return [f"API JSON 不存在：{path}"]
        actual_hash = sha256_file(path)
        if actual_hash != definition.sha256:
            errors.append(f"SHA-256 不匹配：expected={definition.sha256} actual={actual_hash}")
        try:
            workflow = self.load_workflow(definition)
        except (OSError, json.JSONDecodeError) as exc:
            return errors + [f"JSON 无法解析：{exc}"]
        for name, binding in definition.parameters.items():
            for target in [binding, *binding.mirrors]:
                node = workflow.get(target.node_id)
                if not isinstance(node, dict):
                    errors.append(f"参数 {name} 的节点不存在：{target.node_id}")
                    continue
                inputs = node.get("inputs")
                if not isinstance(inputs, dict) or target.input not in inputs:
                    errors.append(f"参数 {name} 的输入不存在：{target.node_id}.{target.input}")
        for node_id in definition.output_nodes:
            if node_id not in workflow:
                errors.append(f"输出节点不存在：{node_id}")
        if definition.save_node not in workflow:
            errors.append(f"保存节点不存在：{definition.save_node}")
        return errors

    def validate_all(self) -> dict[str, list[str]]:
        return {item.workflow_id: self.validate(item.workflow_id) for item in self.list()}

    def prepare(
        self,
        request: GenerationRequest,
        job_id: str,
        index: int,
        uploaded_images: list[str] | None = None,
    ) -> tuple[WorkflowDefinition, dict[str, Any], dict[str, Any]]:
        definition = self.get(request.workflow_id)
        local_errors = self.validate(request.workflow_id)
        if local_errors:
            raise WorkflowValidationError("；".join(local_errors))
        if definition.mode in {"img2img", "incontext"} and not request.input_images:
            raise WorkflowValidationError(f"{definition.workflow_id} 必须提供参考图")
        if definition.mode not in {"img2img", "incontext"} and request.input_images:
            raise WorkflowValidationError(f"{definition.workflow_id} 不接受参考图")

        seed = request.seed
        if seed is None or seed == -1:
            seed = secrets.randbelow(2**63)
        elif index:
            seed = (seed + index) % (2**64)

        values: dict[str, Any] = {"prompt": request.prompt, "seed": seed}
        for key in ("negative_prompt", "width", "height", "steps", "cfg", "denoise"):
            value = getattr(request, key)
            if value is not None:
                values[key] = value
        if uploaded_images:
            values["input_image"] = uploaded_images[0]

        workflow = deepcopy(self.load_workflow(definition))
        for name, value in values.items():
            binding = definition.parameters.get(name)
            if binding is None:
                raise WorkflowValidationError(f"工作流不接受参数：{name}")
            self._apply(workflow, binding, value)

        safe_id = definition.workflow_id.replace(".", "-")
        label = f"{request.output_label.strip().replace(' ', '_')}_" if request.output_label else ""
        prefix = (
            f"comfyui-demo/{date.today().isoformat()}/{safe_id}/{label}{job_id}_{seed}_{index + 1}"
        )
        save_inputs = workflow[definition.save_node]["inputs"]
        if "filename_prefix" not in save_inputs:
            raise WorkflowValidationError(f"保存节点缺少 filename_prefix：{definition.save_node}")
        save_inputs["filename_prefix"] = prefix
        return definition, workflow, {**values, "output_prefix": prefix, "index": index + 1}

    @staticmethod
    def _apply(workflow: dict[str, Any], binding: ParameterBinding, value: Any) -> None:
        targets = [binding, *binding.mirrors]
        for target in targets:
            workflow[target.node_id]["inputs"][target.input] = value
