from __future__ import annotations

import json
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .errors import WorkflowValidationError
from .registry import WorkflowDefinition, WorkflowRegistry, sha256_file

PRESET_FORMAT = "dsh-comfyui-workflow-preset"
PRESET_VERSION = 1


def _parameter_type(binding_type: str) -> str:
    return "number" if binding_type in {"integer", "number"} else "string"


def _parameters(definition: WorkflowDefinition, workflow: dict[str, Any]) -> list[dict[str, Any]]:
    labels = {
        "prompt": "提示词",
        "negative_prompt": "负面提示词",
        "seed": "随机种子",
        "width": "宽度",
        "height": "高度",
        "steps": "采样步数",
        "cfg": "CFG",
        "denoise": "重绘强度",
        "input_image": "参考图",
    }
    result: list[dict[str, Any]] = []
    for name, binding in definition.parameters.items():
        targets = [(binding.node_id, binding.input, False)] + [
            (mirror.node_id, mirror.input, True) for mirror in binding.mirrors
        ]
        for node_id, input_key, is_mirror in targets:
            default = workflow[node_id]["inputs"][input_key]
            item: dict[str, Any] = {
                "id": str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"comfyui-demo:{definition.workflow_id}:{name}:{node_id}:{input_key}",
                    )
                ),
                "name": name,
                "label": labels.get(name, name) + ("（同步）" if is_mirror else ""),
                "type": _parameter_type(binding.type),
                "nodeId": node_id,
                "inputKey": input_key,
                "default": default,
                "description": f"comfyui-demo 注册参数：{name}",
            }
            if binding.type == "integer":
                item["numberKind"] = "int"
            elif binding.type == "number":
                item["numberKind"] = "float"
            if binding.minimum is not None:
                item["min"] = binding.minimum
            if binding.maximum is not None:
                item["max"] = binding.maximum
            if binding.multiple_of is not None:
                item["step"] = binding.multiple_of
            if name == "seed" and not is_mirror:
                item["random"] = True
            if binding.type == "image":
                item["upload"] = "image"
                item["subfolder"] = "comfyui-demo"
            result.append(item)
    return result


def _skill_entry(definition: WorkflowDefinition, root: Path) -> tuple[dict[str, Any], bytes]:
    path = (root / definition.dsh.skill_path).resolve()
    content = path.read_bytes()
    return {"files": [{"path": "SKILL.md", "size": len(content)}], "dirs": []}, content


def build_bundle(output: Path | None = None, version: str = "0.1.0") -> Path:
    registry = WorkflowRegistry(PROJECT_ROOT)
    output = output or (
        PROJECT_ROOT
        / "integrations"
        / "dsh"
        / "releases"
        / f"comfyui-demo-dsh-presets-v{version}.zip"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    workflows: list[dict[str, Any]] = []
    skill_files: dict[str, bytes] = {}
    checksums: dict[str, str] = {}
    for definition in registry.list():
        errors = registry.validate(definition.workflow_id)
        if errors:
            raise WorkflowValidationError("；".join(errors))
        workflow = registry.load_workflow(definition)
        skill, skill_content = _skill_entry(definition, PROJECT_ROOT)
        workflows.append(
            {
                "id": definition.workflow_id,
                "name": f"{definition.title} [comfyui-demo {version}]",
                "description": (
                    f"项目注册工作流 {definition.workflow_id}；版本 {definition.version}；"
                    f"SHA-256 {definition.sha256}。输出只保存在 ComfyUI 权威图库。"
                ),
                "tags": [*definition.dsh.tags, "comfyui-demo", f"v{version}"],
                "parameters": _parameters(definition, workflow),
                "requireSkill": definition.dsh.require_skill,
                "skill": skill,
                "workflow": workflow,
            }
        )
        skill_files[f"skills/{definition.workflow_id}/SKILL.md"] = skill_content
        checksums[definition.workflow_id] = definition.sha256
    manifest = {
        "format": PRESET_FORMAT,
        "version": PRESET_VERSION,
        "exportedAt": datetime.now(UTC).isoformat(),
        "pluginVersion": "0.5.5",
        "count": len(workflows),
        "workflows": workflows,
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("preset.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("checksums.json", json.dumps(checksums, ensure_ascii=False, indent=2))
        for name, content in skill_files.items():
            archive.writestr(name, content)
    return output


def verify_bundle(path: Path) -> dict[str, Any]:
    registry = WorkflowRegistry(PROJECT_ROOT)
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "preset.json" not in names:
            raise WorkflowValidationError("ZIP 缺少 preset.json")
        manifest = json.loads(archive.read("preset.json"))
        if manifest.get("format") != PRESET_FORMAT or manifest.get("version") != PRESET_VERSION:
            raise WorkflowValidationError("DSH preset 格式或版本不正确")
        workflows = manifest.get("workflows")
        if not isinstance(workflows, list) or manifest.get("count") != len(workflows):
            raise WorkflowValidationError("DSH preset count 与工作流数量不一致")
        expected_ids = {item.workflow_id for item in registry.list()}
        actual_ids = {item.get("id") for item in workflows}
        if actual_ids != expected_ids:
            raise WorkflowValidationError(f"DSH 工作流集合不一致：{actual_ids}")
        for item in workflows:
            workflow_id = item["id"]
            skill_path = f"skills/{workflow_id}/SKILL.md"
            if skill_path not in names:
                raise WorkflowValidationError(f"技能包文件缺失：{skill_path}")
            expected = registry.load_workflow(registry.get(workflow_id))
            if item.get("workflow") != expected:
                raise WorkflowValidationError(f"DSH 工作流内容不一致：{workflow_id}")
        checksums = json.loads(archive.read("checksums.json"))
        for definition in registry.list():
            if checksums.get(definition.workflow_id) != definition.sha256:
                raise WorkflowValidationError(f"DSH 哈希声明不一致：{definition.workflow_id}")
    return {
        "ok": True,
        "path": str(path.resolve()),
        "count": len(workflows),
        "sha256": sha256_file(path),
    }


def backup_dsh_store(store_path: Path, output: Path) -> Path:
    raw = json.loads(store_path.read_text(encoding="utf-8"))
    records = raw if isinstance(raw, list) else [raw]
    workflows = []
    for record in records:
        workflows.append(
            {
                "id": record["id"],
                "name": record["name"],
                "description": record.get("description", ""),
                "tags": record.get("tags", []),
                "parameters": record.get("parameters", []),
                "requireSkill": bool(record.get("requireSkill", False)),
                "skill": None,
                "workflow": record["workflow"],
            }
        )
    manifest = {
        "format": PRESET_FORMAT,
        "version": PRESET_VERSION,
        "exportedAt": datetime.now(UTC).isoformat(),
        "pluginVersion": "0.5.5",
        "count": len(workflows),
        "workflows": workflows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("preset.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return output
