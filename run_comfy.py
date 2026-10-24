"""Legacy entry point. Prefer `comfy-demo run`."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.models import GenerationRequest
from comfyui_agent_studio.service import GenerationService

WORKFLOW_ALIASES = {
    "anima_t2i.json": "anima.standard.v1",
    "anima_hq.json": "anima.hq-2x.v1",
    "animagine_t2i.json": "animagine.standard.v1",
    "larkie_img2img.json": "larkie.img2img.v1",
    "larkie_incontext.json": "larkie.incontext.v1",
    "anima.standard.v1.json": "anima.standard.v1",
    "anima.hq-2x.v1.json": "anima.hq-2x.v1",
    "animagine.standard.v1.json": "animagine.standard.v1",
    "larkie.img2img.v1.json": "larkie.img2img.v1",
    "larkie.incontext.v1.json": "larkie.incontext.v1",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="兼容入口；新项目请使用 comfy-demo run")
    parser.add_argument("--workflow", default="animagine_t2i.json")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--cfg", type=float)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--prefix")
    parser.add_argument("--out")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--sampler")
    parser.add_argument("--scheduler")
    parser.add_argument("--input-image", action="append", type=Path, default=[])
    args = parser.parse_args()

    workflow_id = WORKFLOW_ALIASES.get(Path(args.workflow).name)
    if workflow_id is None:
        parser.error("仅支持注册表中的 5 条工作流；请改用 comfy-demo workflow list")
    if args.sampler or args.scheduler:
        parser.error("sampler/scheduler 尚未在注册表公开，不能静默修改")
    if args.server != "http://127.0.0.1:8188":
        os.environ["COMFY_DEMO_COMFYUI_URL"] = args.server
    if args.out:
        print("迁移提示：--out 已停用；结果只保存在 ComfyUI 权威输出目录。")
    print("迁移提示：run_comfy.py 已转调统一核心；推荐使用 comfy-demo run。")
    request = GenerationRequest(
        workflow_id=workflow_id,
        prompt=args.prompt,
        negative_prompt=args.negative,
        seed=args.seed,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg=args.cfg,
        input_images=args.input_image,
        output_label=args.prefix,
        client="cli",
    )
    manifest = GenerationService(load_settings()).submit(request, wait=True)
    print(manifest.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
