"""Legacy hot-folder entry point. Prefer `comfy-demo watch`."""

from comfyui_agent_studio.config import load_settings
from comfyui_agent_studio.inbox import InboxWatcher
from comfyui_agent_studio.service import GenerationService


def main() -> int:
    watcher = InboxWatcher(GenerationService(load_settings()))
    print(f"迁移提示：inbox_watch.py 已转调统一核心。监听 {watcher.root / 'pending'}")
    watcher.watch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
