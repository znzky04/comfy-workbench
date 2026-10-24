"""Legacy DSH workflow entry point backed by the project registry."""

from __future__ import annotations

import argparse

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.models import GenerationRequest
from comfyui_agent_studio.service import GenerationService


def main() -> int:
    parser = argparse.ArgumentParser(description="兼容入口；不再读取 DSH 私有 workflows.json")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--seed", type=int, default=31337)
    parser.add_argument("--landscape", action="store_true")
    parser.add_argument("--prefix", default="legacy-main-anima")
    parser.add_argument("--steps", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.out:
        print("迁移提示：--out 已停用；不会复制 ComfyUI 输出。")
    print("迁移提示：已使用 anima.standard.v1，旧 DSH 主Anima 不再是隐藏依赖。")
    width, height = (1536, 1024) if args.landscape else (1024, 1536)
    request = GenerationRequest(
        workflow_id="anima.standard.v1",
        prompt=args.prompt,
        seed=args.seed,
        width=width,
        height=height,
        steps=args.steps,
        output_label=args.prefix,
        client="cli",
    )
    manifest = GenerationService(load_settings()).submit(request, wait=True)
    print(manifest.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
