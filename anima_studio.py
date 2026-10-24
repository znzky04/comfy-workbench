"""Legacy studio entry point. Prefer `comfy-demo studio`."""

import sys

from comfyui_agent_studio.cli import app

if __name__ == "__main__":
    print("迁移提示：anima_studio.py 已转调统一 CLI，不会启动 ComfyUI。")
    sys.argv = [sys.argv[0], "studio"]
    app()
