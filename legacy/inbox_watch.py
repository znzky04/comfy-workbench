#!/usr/bin/env python
"""热文件夹：把提示词丢进 inbox/，自动出图到 output/。

丢一个 .txt（或 .json），内容示例：

    prompt: 1girl, solo, silver hair, ...
    negative: low quality, bad hands
    size: 1024x1536
    steps: 30
    cfg: 5
    seed: -1
    count: 2

也可以只写一行提示词（其它用默认值）。处理完的 txt 会被移到 inbox/done/。
启动：双击 启动监听.bat
"""

from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path

from anima_studio import (
    OUTPUT,
    build_workflow,
    download,
    ensure_server,
    post_json,
    server_alive,
    wait_for_history,
)

HERE = Path(__file__).resolve().parent
INBOX = HERE / "inbox"
DONE = INBOX / "done"
SETTLE = 1.5  # 文件写入后等它稳定，避免读到半个文件


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    params = {"prompt": "", "negative": "", "width": 1024, "height": 1536, "steps": 30, "cfg": 5.0, "seed": -1, "count": 1}
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        params.update({k: v for k, v in data.items() if k in params})
        return params
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key, value = key.strip().lower(), value.strip()
            if key == "size" and "x" in value:
                params["width"], params["height"] = (int(v) for v in value.split("x"))
            elif key in params and key not in ("width", "height"):
                params[key] = value
        elif line.strip():
            params["prompt"] = (params["prompt"] + " " + line.strip()).strip()
    if not params["prompt"]:
        raise ValueError("没有读到提示词")
    params["steps"] = int(float(params["steps"]))
    params["cfg"] = float(params["cfg"])
    params["count"] = max(1, int(params["count"]))
    base_seed = int(params["seed"])
    params["seed"] = base_seed if base_seed >= 0 else random.randint(1, 2**53 - 1)
    return params


def run(params: dict) -> list[Path]:
    seed = params.pop("seed")
    count = params.pop("count")
    results: list[Path] = []
    for index in range(count):
        job = dict(params)
        job["seed"] = seed + index if seed else random.randint(1, 2**53 - 1)
        submitted = post_json(f"{SERVER_URL}/prompt", {"prompt": build_workflow(job), "client_id": f"inbox-{index}"})
        if submitted.get("node_errors"):
            raise RuntimeError(json.dumps(submitted["node_errors"], ensure_ascii=False))
        entry = wait_for_history(submitted["prompt_id"])
        for out in entry.get("outputs", {}).values():
            for image in out.get("images", []) or []:
                results.append(download(image, OUTPUT))
        print(f"  第 {index + 1}/{count} 张完成", flush=True)
    return results


SERVER_URL = "http://127.0.0.1:8188"


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    print(f"监听 {INBOX} …把 .txt / .json 丢进去就会出图。", flush=True)
    print(f"ComfyUI: {'已连接' if server_alive() else '正在启动…'}", flush=True)
    ensure_server()
    seen: dict[Path, float] = {}
    while True:
        for path in sorted(INBOX.iterdir()):
            if path.is_dir() or path.suffix.lower() not in (".txt", ".json"):
                continue
            stamp = path.stat().st_mtime
            if seen.get(path) != stamp:
                seen[path] = stamp
                continue  # 等一轮，确认文件写完
            if time.time() - stamp < SETTLE:
                continue
            print(f"接到 {path.name}", flush=True)
            try:
                params = parse(path)
                files = run(params)
                for file in files:
                    print(f"  → {file}", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"  失败: {exc}", flush=True)
            finally:
                seen.pop(path, None)
                if path.exists():
                    shutil.move(str(path), str(DONE / f"{int(time.time())}_{path.name}"))
        time.sleep(1.0)


if __name__ == "__main__":
    raise SystemExit(main())
