---
name: anima-standard
description: 使用 Anima 标准工作流进行常规二次元文生图。
---

# Anima Standard

适合角色立绘和常规二次元场景。运行前确认 ComfyUI Desktop 已由用户启动。

- `prompt` 必填；不要在参数外偷偷修改节点。
- 默认竖图尺寸来自工作流，可按 8 的倍数调整到 256–2048。
- `seed=0` 是合法固定种子；仅省略 seed 才随机。
- 输出位于 ComfyUI 的 `output/comfyui-demo/`，不要复制或删除。
- 连接失败时提示用户打开 Desktop，不要自行启动或强杀进程。
