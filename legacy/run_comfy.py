#!/usr/bin/env python
"""ComfyUI 最小客户端：提交 API 格式工作流、轮询、下载结果。

用法示例：
    python run_comfy.py --prompt "1girl, ... " --width 832 --height 1216
    python run_comfy.py --workflow my_api_workflow.json --prompt "..." --seed 1234

只依赖标准库。要求 ComfyUI 已启动（默认 http://127.0.0.1:8188）。
工作流必须是 ComfyUI 的 "Save (API Format)" 导出的 JSON；
如果是编辑器里保存的普通 JSON（含 nodes/links），请先在 ComfyUI 里导出 API 格式。
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SAMPLERS = ("KSampler", "KSamplerAdvanced")
LATENTS = ("EmptyLatentImage", "EmptySD3LatentImage", "EmptyLatentImagePresets")


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_node(workflow: dict, class_types: tuple[str, ...]) -> tuple[str, dict] | None:
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") in class_types:
            return node_id, node
    return None


def linked_node(workflow: dict, link) -> tuple[str, dict] | None:
    """把 ["12", 0] 这样的连线解析成 (node_id, node)。"""
    if isinstance(link, list) and link and isinstance(link[0], str):
        node = workflow.get(link[0])
        if isinstance(node, dict):
            return link[0], node
    return None


def patch_workflow(workflow: dict, args) -> list[str]:
    notes: list[str] = []

    sampler = find_node(workflow, SAMPLERS)
    if sampler and sampler[1].get("inputs"):
        inputs = sampler[1]["inputs"]
        if args.seed is not None:
            inputs["seed"] = args.seed if args.seed >= 0 else random.randint(1, 2**53 - 1)
            notes.append(f"seed={inputs['seed']}")
        if args.steps is not None:
            inputs["steps"] = args.steps
        if args.cfg is not None:
            inputs["cfg"] = args.cfg
        if args.sampler:
            inputs["sampler_name"] = args.sampler
        if args.scheduler:
            inputs["scheduler"] = args.scheduler

        if args.prompt:
            target = linked_node(workflow, inputs.get("positive"))
            if target and "text" in target[1].get("inputs", {}):
                target[1]["inputs"]["text"] = args.prompt
                notes.append(f"positive <- node {target[0]}")
            else:
                notes.append("警告: 正向提示词节点不是简单 CLIPTextEncode，未覆盖")

        if args.negative:
            target = linked_node(workflow, inputs.get("negative"))
            if target and "text" in target[1].get("inputs", {}):
                target[1]["inputs"]["text"] = args.negative
                notes.append(f"negative <- node {target[0]}")
    else:
        notes.append("警告: 工作流里没找到 KSampler，提示词/种子未覆盖")

    latent = find_node(workflow, LATENTS)
    if latent and (args.width or args.height):
        inputs = latent[1].setdefault("inputs", {})
        if args.width:
            inputs["width"] = args.width
        if args.height:
            inputs["height"] = args.height
        notes.append(f"size={inputs.get('width')}x{inputs.get('height')}")

    if args.prefix:
        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") in ("SaveImage", "PreviewImage"):
                node.setdefault("inputs", {})["filename_prefix"] = args.prefix
        notes.append(f"prefix={args.prefix}")

    return notes


def wait_for_history(server: str, prompt_id: str, timeout: float) -> dict:
    deadline = time.time() + timeout
    last_log = 0.0
    while time.time() < deadline:
        history = get_json(f"{server}/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"执行失败: {json.dumps(status, ensure_ascii=False)}")
            if status.get("completed", True):
                return entry
        if time.time() - last_log > 10:
            last_log = time.time()
            try:
                queue = get_json(f"{server}/queue")
                running = len(queue.get("queue_running", []))
                pending = len(queue.get("queue_pending", []))
                print(f"  ...运行中 {running} / 排队 {pending}", flush=True)
            except Exception:
                pass
        time.sleep(1.5)
    raise TimeoutError(f"{timeout:.0f}s 内没有完成，prompt_id={prompt_id}")


def collect_images(entry: dict) -> list[dict]:
    images = []
    for node_output in entry.get("outputs", {}).values():
        images.extend(node_output.get("images", []) or [])
    return images


def download(server: str, image: dict, out_dir: Path) -> Path:
    query = urllib.parse.urlencode(
        {"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")}
    )
    with urllib.request.urlopen(f"{server}/view?{query}", timeout=120) as resp:
        blob = resp.read()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / Path(image["filename"]).name
    path.write_bytes(blob)
    return path


def main() -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="提交 ComfyUI 工作流并下载生成结果")
    parser.add_argument("--workflow", default=str(here / "animagine_t2i.json"), help="API 格式工作流 JSON")
    parser.add_argument("--server", default="http://127.0.0.1:8188", help="ComfyUI 地址")
    parser.add_argument("--prompt", help="正向提示词")
    parser.add_argument("--negative", help="负向提示词")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--cfg", type=float)
    parser.add_argument("--sampler")
    parser.add_argument("--scheduler")
    parser.add_argument("--seed", type=int, default=-1, help="-1 表示随机")
    parser.add_argument("--prefix", default="dsh_comfy", help="输出文件名前缀")
    parser.add_argument("--out", default=str(here / "output"), help="下载到哪个目录")
    parser.add_argument("--timeout", type=float, default=600, help="等待生成完成的秒数")
    args = parser.parse_args()

    server = args.server.rstrip("/")
    workflow = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    if "nodes" in workflow and "links" in workflow:
        raise SystemExit("这是编辑器格式的工作流。请在 ComfyUI 里用「Save (API Format) / 导出(API)」重新导出。")

    notes = patch_workflow(workflow, args)
    print("已应用的覆盖:", "; ".join(notes) if notes else "(无)", flush=True)

    submitted = post_json(f"{server}/prompt", {"prompt": workflow, "client_id": f"comfy-cli-{uuid.uuid4().hex[:8]}"})
    if submitted.get("node_errors"):
        raise SystemExit(f"节点校验失败: {json.dumps(submitted['node_errors'], ensure_ascii=False)}")

    prompt_id = submitted["prompt_id"]
    print(f"prompt_id={prompt_id}，等待生成...", flush=True)
    started = time.time()
    entry = wait_for_history(server, prompt_id, args.timeout)

    images = collect_images(entry)
    if not images:
        print("没有产出图片（检查工作流是否包含 SaveImage/PreviewImage 输出节点）")
        return 1

    paths = [download(server, image, Path(args.out)) for image in images]
    print(json.dumps(
        {
            "success": True,
            "prompt_id": prompt_id,
            "elapsed_sec": round(time.time() - started, 1),
            "outputs": [str(p) for p in paths],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
