# Codex 使用 ComfyUI Agent Studio

## 前置条件

用户自行打开 ComfyUI Desktop，确认地址为 `http://127.0.0.1:8188`。Codex 不启动、强杀或更新 ComfyUI，也不在未确认时下载模型、安装节点或调用付费 API。

官方 comfy-mcp 使用的 comfy-cli 默认工作区必须对应用户实际实例。以下仅为维护者历史配置，新用户替换为自己的目录：

```text
E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI
```

只读核对使用 `comfy --json which`。若配置漂移，可在不启动服务的情况下运行：

```powershell
comfy --skip-prompt set-default "E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI"
```

## 官方 comfy-mcp 固定流程

1. `server_info`：确认服务可连接及版本。
2. `system_stats`：确认队列和显存；HQ/超分前必须检查显存。
3. `validate_workflow`：使用 `workflows/registry.json` 指向的 API JSON 校验。
4. `run_workflow(wait=false)`：异步提交，参数只能来自注册表。
5. `job(wait/status)`：等待或查询任务。
6. `fetch_outputs` 或直接报告 ComfyUI 返回的权威绝对路径。

## 一致性规则

- 每次运行前核对注册表 SHA-256；工作流哈希不匹配时停止。
- `seed=0` 必须按 0 提交；仅缺省或 `-1` 随机。
- img2img 与 in-context 必须提供有效参考图。
- 未注册参数必须拒绝，不能静默忽略。
- 所有原图、失败图和未采用图都保留；不得调用删除。
- 本地视频不是默认路径。
- Codex 运行结果必须写入项目 manifest，或将 MCP 结果人工补录为等价记录。

## 注册工作流

- `anima.standard.v1`
- `anima.hq-2x.v1`
- `animagine.standard.v1`
- `larkie.img2img.v1`
- `larkie.incontext.v1`

HQ、拉琪 img2img 和拉琪 in-context 运行前应先阅读对应 DSH 技能说明，因为其中包含显存、参考图和身份保持约束。
