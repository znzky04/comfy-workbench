#!/usr/bin/env python
"""用插件库里提取的「主Anima」原工作流出图（抽签默认关闭）。

这个脚本直接读 dsh-comfyui 的工作流库，保持原图节点结构不变，只覆盖
提示词 / 种子 / 横竖版 / 输出前缀。用法：

    python gen_from_their_workflow.py --prompt "1girl, solo, ..." --seed 31337
    python gen_from_their_workflow.py --prompt "..." --landscape --prefix uika_b
"""

from __future__ import annotations

raise SystemExit("历史实现已禁用。请使用根目录兼容入口；不读取 DSH 私有工作流库。")

import argparse
import copy
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

STORE = pathlib.Path.home() / ".dsh" / "data" / "dsh-comfyui" / "workflows.json"
SERVER = "http://127.0.0.1:8188"
OUT = pathlib.Path(r"E:\AI\Deepseek\comfyui-demo\kurumi")

PROMPT_NODE = "39"      # PrimitiveStringMultiline：用户提示词
SAMPLER = "8"
LATENT_PORTRAIT = "12"
ORIENT_SWITCH = "126"   # false=1024x1536, true=1536x1024
RAFFLE_SWITCH = "128"   # 原工作流里 true，抽签池含成人标签，默认关掉
PREFIX_NODE = "97"
SAVE_NODE = "94"


def post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


def get(url: str) -> dict:
    return json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))


def load_base(name_prefix: str = "主Anima") -> dict:
    data = json.loads(STORE.read_text(encoding="utf-8"))
    for entry in data:
        if entry["name"].startswith(name_prefix):
            return repair(entry["workflow"])
    raise SystemExit(f"工作流库里没有 {name_prefix}")


def repair(wf: dict) -> dict:
    """修提取器留下的两处接线错误（原图 132 被丢掉、109 的 clip 接错槽位）。"""
    wf.setdefault(
        "132",
        {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["110", 0],
                "clip": ["110", 1],
                "lora_name": "anima-highres-aesthetic-boost.safetensors",
                "strength_model": 0.5,
                "strength_clip": 0.5,
            },
        },
    )
    wf["109"]["inputs"]["model"] = ["132", 0]
    wf["109"]["inputs"]["clip"] = ["132", 1]
    return wf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, default=31337)
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--prefix", default="uika")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    wf = copy.deepcopy(load_base())
    wf[RAFFLE_SWITCH]["inputs"]["switch"] = False
    wf[PROMPT_NODE]["inputs"]["value"] = args.prompt
    wf[SAMPLER]["inputs"]["seed"] = args.seed
    wf[ORIENT_SWITCH]["inputs"]["switch"] = bool(args.landscape)
    wf[PREFIX_NODE]["inputs"]["value"] = args.prefix
    # SaveImage 的 filename_prefix 在原图里是「开关 -> PrimitiveString」的连线，
    # 提取后这个连线在某些版本上会让输出目录落在意料之外，这里直接给字面量。
    wf[SAVE_NODE]["inputs"]["filename_prefix"] = args.prefix
    if args.steps:
        wf[SAMPLER]["inputs"]["steps"] = args.steps

    print(f"提交 {args.prefix} (seed={args.seed}, landscape={args.landscape})", flush=True)
    started = time.time()
    submitted = post(f"{SERVER}/prompt", {"prompt": wf, "client_id": "dsh-uika-test"})
    prompt_id = submitted["prompt_id"]

    while True:
        history = get(f"{SERVER}/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            if entry["status"]["status_str"] != "success":
                print(json.dumps(entry["status"], ensure_ascii=False)[:800], flush=True)
                return 1
            break
        time.sleep(2)

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for node_out in entry["outputs"].values():
        for image in node_out.get("images", []):
            query = urllib.parse.urlencode(
                {"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": "output"}
            )
            blob = urllib.request.urlopen(f"{SERVER}/view?{query}", timeout=120).read()
            path = out_dir / f"{args.prefix}.png"
            path.write_bytes(blob)
            print(f"  -> {path}  {len(blob)//1024} KB  {round(time.time()-started,1)}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
