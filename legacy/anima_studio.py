#!/usr/bin/env python
"""Anima 本地画图台 —— 不经过任何 Agent，浏览器里填提示词就出图。

启动：双击 启动画图台.bat，或
    python anima_studio.py
然后打开 http://127.0.0.1:8199

它做的事：确保 ComfyUI 在 8188 跑着（没跑就自动拉起）→ 把提示词灌进
anima_t2i.json → 提交 → 轮询 → 把图下载到 output/ → 网页里显示。
"""

from __future__ import annotations

raise SystemExit("历史实现已禁用。请在仓库根目录运行 comfy-demo studio；Desktop 需手动启动。")

import json
import os
import queue
import random
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ---------------------------------------------------------------- 路径配置
HERE = Path(__file__).resolve().parent
COMFY_DIR = Path(r"E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI")
COMFY_PY = COMFY_DIR / ".venv" / "Scripts" / "python.exe"
COMFY_MAIN = COMFY_DIR / "main.py"
WORKFLOW = HERE / "anima_t2i.json"
WORKFLOWS = {
    "anima_t2i.json": "标准 — 1024×1536，约 60 秒",
    "anima_hq.json": "2× 超分 — 最终 2048×3072，约 4 分钟",
}
OUTPUT = HERE / "output"
LOG = HERE / "comfyui-server.log"
SERVER = "http://127.0.0.1:8188"
PORT = 8199

POS_ID, NEG_ID, LATENT_ID, SAMPLER_ID, SAVE_ID = "20", "21", "30", "40", "60"

DEFAULT_NEG = (
    "worst quality, low quality, score_1, score_2, score_3, fused fingers, "
    "bad anatomy, malformed limbs, blurry, lowres, jpeg artifacts, uncanny"
)

# ---------------------------------------------------------------- ComfyUI 通信


def get_json(url: str, timeout: float = 10):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: float = 60):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def server_alive() -> bool:
    try:
        get_json(f"{SERVER}/system_stats", timeout=3)
        return True
    except Exception:
        return False


def ensure_server(wait: float = 240) -> bool:
    if server_alive():
        return True
    if not COMFY_PY.exists():
        return False
    flags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags = subprocess.CREATE_NEW_PROCESS_GROUP
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"          # 0.42+ 的自定义节点警告可能带 emoji，
    env["PYTHONIOENCODING"] = "utf-8"  # GBK 编码的 stderr 会让启动直接崩
    with LOG.open("ab") as log:
        subprocess.Popen(
            [str(COMFY_PY), str(COMFY_MAIN), "--port", "8188", "--listen", "127.0.0.1", "--disable-auto-launch"],
            cwd=str(COMFY_DIR),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            env=env,
        )
    deadline = time.time() + wait
    while time.time() < deadline:
        if server_alive():
            return True
        time.sleep(2)
    return False


def wait_for_history(prompt_id: str, timeout: float = 900) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        history = get_json(f"{SERVER}/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI 执行报错")
            if status.get("completed", True):
                return entry
        time.sleep(1.5)
    raise TimeoutError("生成超时")


def download(image: dict, out_dir: Path) -> Path:
    query = urllib.parse.urlencode(
        {"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")}
    )
    with urllib.request.urlopen(f"{SERVER}/view?{query}", timeout=120) as resp:
        blob = resp.read()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / Path(image["filename"]).name
    path.write_bytes(blob)
    return path


def build_workflow(params: dict) -> dict:
    path = HERE / params.get("workflow_file", WORKFLOW.name)
    wf = json.loads(path.read_text(encoding="utf-8"))
    wf[POS_ID]["inputs"]["text"] = params["prompt"]
    wf[NEG_ID]["inputs"]["text"] = params["negative"] or DEFAULT_NEG
    wf[LATENT_ID]["inputs"]["width"] = params["width"]
    wf[LATENT_ID]["inputs"]["height"] = params["height"]
    sampler = wf[SAMPLER_ID]["inputs"]
    sampler["seed"] = params["seed"]
    sampler["steps"] = params["steps"]
    sampler["cfg"] = params["cfg"]
    wf[SAVE_ID]["inputs"]["filename_prefix"] = "anima"
    return wf


# ---------------------------------------------------------------- 任务队列
JOBS: list[dict] = []
JOBS_LOCK = threading.Lock()
TASK_QUEUE: "queue.Queue[dict]" = queue.Queue()


def worker() -> None:
    while True:
        job = TASK_QUEUE.get()
        try:
            job["status"] = "running"
            job["started"] = time.time()
            wf = build_workflow(job["params"])
            submitted = post_json(f"{SERVER}/prompt", {"prompt": wf, "client_id": f"studio-{uuid.uuid4().hex[:6]}"})
            if submitted.get("node_errors"):
                raise RuntimeError(json.dumps(submitted["node_errors"], ensure_ascii=False))
            entry = wait_for_history(submitted["prompt_id"])
            images = [img for out in entry.get("outputs", {}).values() for img in out.get("images", []) or []]
            job["images"] = [download(img, OUTPUT).name for img in images]
            job["status"] = "done"
            job["elapsed"] = round(time.time() - job["started"], 1)
        except Exception as exc:  # noqa: BLE001
            job["status"] = "error"
            job["error"] = str(exc)
        finally:
            job["finished"] = time.time()
            TASK_QUEUE.task_done()


def add_job(params: dict) -> str:
    job = {"id": uuid.uuid4().hex[:8], "status": "queued", "params": params, "images": [], "created": time.time()}
    with JOBS_LOCK:
        JOBS.append(job)
        if len(JOBS) > 200:
            del JOBS[:-200]
    TASK_QUEUE.put(job)
    return job["id"]


# ---------------------------------------------------------------- HTTP 服务
PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anima 画图台</title>
<style>
  :root { --bg:#0d1117; --panel:#161b22; --line:#2a3140; --text:#e6edf3; --dim:#8b949e; --accent:#7c9cff; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif; }
  header { padding:18px 24px; border-bottom:1px solid var(--line); display:flex; align-items:baseline; gap:12px; }
  header h1 { font-size:17px; margin:0; font-weight:600; letter-spacing:.5px; }
  header span { color:var(--dim); font-size:12px; }
  .wrap { display:grid; grid-template-columns:420px 1fr; gap:20px; padding:20px 24px; align-items:start; }
  @media (max-width:900px){ .wrap{ grid-template-columns:1fr; } }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:16px; }
  label { display:block; font-size:12px; color:var(--dim); margin:12px 0 6px; }
  textarea, input, select { width:100%; background:#0d1117; color:var(--text); border:1px solid var(--line);
    border-radius:6px; padding:8px 10px; font:inherit; resize:vertical; }
  textarea { min-height:110px; }
  .row { display:grid; grid-template-columns:1.5fr .8fr .8fr; gap:8px; }
  .row.two { grid-template-columns:repeat(2,1fr); }
  button { width:100%; margin-top:16px; padding:11px; border:0; border-radius:7px; cursor:pointer;
    background:linear-gradient(180deg,#8aa4ff,#6c8cff); color:#0b1020; font-weight:700; font-size:14px; }
  button:disabled { opacity:.55; cursor:default; }
  .hint { color:var(--dim); font-size:12px; margin-top:10px; }
  #status { font-size:12px; color:var(--dim); margin-top:10px; min-height:18px; }
  .gallery { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; }
  figure { margin:0; background:var(--panel); border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  figure img { width:100%; display:block; cursor:zoom-in; }
  figcaption { padding:8px 10px; font-size:12px; color:var(--dim); border-top:1px solid var(--line); }
  figcaption b { color:var(--text); font-weight:500; display:block; margin-bottom:4px; }
  .empty { color:var(--dim); text-align:center; padding:60px 0; font-size:13px; }
  #lightbox { position:fixed; inset:0; background:#000000e6; display:none; align-items:center; justify-content:center; z-index:9; }
  #lightbox img { max-width:94vw; max-height:94vh; }
</style>
</head>
<body>
<header><h1>Anima 画图台</h1><span id="conn">连接中…</span></header>
<div class="wrap">
  <div class="card">
    <label for="prompt">正向提示词</label>
    <textarea id="prompt" placeholder="masterpiece, best quality, score_9, score_8, 1girl, solo, ..."></textarea>
    <label for="negative">负向提示词</label>
    <textarea id="negative" style="min-height:60px"></textarea>
    <label>流程</label>
    <select id="flow">
      <option value="anima_t2i.json" selected>标准 — 1024×1536，约 60 秒</option>
      <option value="anima_hq.json">2× 超分 — 最终 2048×3072，约 4 分钟</option>
    </select>
    <label>尺寸 / 张数 / 步数</label>
    <div class="row">
      <select id="size">
        <option value="1024x1536" selected>1024×1536 竖</option>
        <option value="1536x1024">1536×1024 横</option>
        <option value="1024x1024">1024×1024 方</option>
        <option value="832x1216">832×1216 竖</option>
      </select>
      <input id="count" type="number" min="1" max="8" value="1" title="张数">
      <input id="steps" type="number" min="4" max="80" value="30" title="步数">
    </div>
    <label>CFG / 种子（-1 随机）</label>
    <div class="row two">
      <input id="cfg" type="number" step="0.5" min="1" max="15" value="5" title="CFG">
      <input id="seed" type="number" value="-1" title="种子，-1 随机">
    </div>
    <button id="go">生 成</button>
    <div id="status"></div>
    <div class="hint">种子 -1 表示随机；连点会排队，一次只跑一张，不会挤爆显存。</div>
  </div>
  <div>
    <div class="gallery" id="gallery"></div>
    <div class="empty" id="empty">还没有图。左边写完提示词，点「生成」。</div>
  </div>
</div>
<div id="lightbox"><img alt=""></div>
<script>
const $ = id => document.getElementById(id);
let busy = false;

async function gen() {
  const [w, h] = $('size').value.split('x').map(Number);
  const count = Math.max(1, Math.min(8, Number($('count').value) || 1));
  for (let i = 0; i < count; i++) {
    const seed = Number($('seed').value);
    await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        prompt: $('prompt').value.trim(),
        negative: $('negative').value.trim(),
        workflow: $('flow').value,
        width: w, height: h,
        steps: Number($('steps').value),
        cfg: Number($('cfg').value),
        seed: seed >= 0 ? seed + i : -1
      })
    });
  }
  poll();
}

async function poll() {
  const r = await fetch('/api/state');
  const s = await r.json();
  $('conn').textContent = s.server ? 'ComfyUI 已连接' : 'ComfyUI 未连接';
  const running = s.jobs.filter(j => j.status === 'running' || j.status === 'queued').length;
  $('status').textContent = running ? `队列中 ${running} 张…` : '';
  $('go').disabled = false;

  const gallery = $('gallery');
  const done = s.jobs.filter(j => j.status === 'done').slice(-24).reverse();
  const pending = s.jobs.filter(j => j.status === 'queued' || j.status === 'running');
  $('empty').style.display = (done.length || pending.length) ? 'none' : 'block';
  let html = '';
  for (const j of pending) {
    html += `<figure><figcaption><b>生成中…</b>${esc(j.params.prompt).slice(0, 80)}</figcaption></figure>`;
  }
  for (const j of done) {
    for (const img of j.images) {
      html += `<figure><img src="/media?name=${encodeURIComponent(img)}" loading="lazy">
        <figcaption><b>${j.params.width}×${j.params.height} · seed ${j.params.seed} · ${j.elapsed ?? ''}s</b>
        ${esc(j.params.prompt).slice(0, 90)}</figcaption></figure>`;
    }
  }
  gallery.innerHTML = html;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

$('go').onclick = gen;
$('gallery').onclick = e => {
  if (e.target.tagName === 'IMG') { $('lightbox').querySelector('img').src = e.target.src; $('lightbox').style.display = 'flex'; }
};
$('lightbox').onclick = () => $('lightbox').style.display = 'none';
setInterval(poll, 2500);
poll();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # 静音访问日志
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/state":
            with JOBS_LOCK:
                jobs = [
                    {
                        "id": j["id"],
                        "status": j["status"],
                        "params": j["params"],
                        "images": j["images"],
                        "elapsed": j.get("elapsed"),
                        "error": j.get("error"),
                    }
                    for j in JOBS
                ]
            payload = json.dumps({"server": server_alive(), "jobs": jobs}, ensure_ascii=False)
            self._send(200, payload.encode("utf-8"), "application/json; charset=utf-8")
        elif parsed.path == "/media":
            name = urllib.parse.parse_qs(parsed.query).get("name", [""])[0]
            target = (OUTPUT / name).resolve()
            if target.parent != OUTPUT.resolve() or not target.is_file():
                self._send(404, b"not found", "text/plain")
                return
            self._send(200, target.read_bytes(), "image/png")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        if urllib.parse.urlparse(self.path).path != "/api/generate":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            self._send(400, json.dumps({"error": "提示词是空的"}, ensure_ascii=False).encode("utf-8"), "application/json")
            return
        seed = int(data.get("seed", -1))
        flow = data.get("workflow") if data.get("workflow") in WORKFLOWS else WORKFLOW.name
        params = {
            "prompt": prompt,
            "negative": (data.get("negative") or "").strip(),
            "workflow_file": flow,
            "width": int(data.get("width", 1024)),
            "height": int(data.get("height", 1536)),
            "steps": int(data.get("steps", 30)),
            "cfg": float(data.get("cfg", 5)),
            "seed": seed if seed >= 0 else random.randint(1, 2**53 - 1),
        }
        job_id = add_job(params)
        self._send(200, json.dumps({"id": job_id}, ensure_ascii=False).encode("utf-8"), "application/json")


class Server(ThreadingHTTPServer):
    allow_reuse_address = False  # Windows 上 True 会让两个进程抢同一端口


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ok = ensure_server()
    threading.Thread(target=worker, daemon=True).start()
    try:
        httpd = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"端口 {PORT} 已被占用——大概已经有一个画图台在跑了，直接开 http://127.0.0.1:{PORT} 即可。", flush=True)
        return 1
    print(f"画图台: http://127.0.0.1:{PORT}  (ComfyUI {'已就绪' if ok else '未就绪，请检查日志'})", flush=True)
    if ok and not os.environ.get("ANIMA_NO_BROWSER"):
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
