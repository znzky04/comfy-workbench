# ComfyUI Agent Studio

一个本地优先、可追溯的 ComfyUI 多入口控制工程。Codex、DSH、CLI、热文件夹和后续本地网页共享同一份版本化注册表、参数校验、任务状态与输出规则。

## 最重要的边界

- 请由用户手动启动、停止和更新 ComfyUI Desktop。
- 本项目只连接 `http://127.0.0.1:8188`，绝不自动启动或强杀 ComfyUI。
- Desktop 当前实例的图片权威位置是 `E:\Comfy-Desktop\ComfyUI-Shared\output\comfyui-demo`。
- 历史 `output/` 与 `kurumi/` 原地保留；新流程不再向项目复制图片。
- 不会自动删除成功图、失败图或未采用图。

## 安装

PowerShell：

```powershell
cd E:\AI\Deepseek\comfyui-demo
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Web 依赖将在 M5 的真实生成门禁通过后单独安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web,dev]"
```

如需本机覆盖，复制 `config.example.toml` 为 `config.local.toml`；该文件不会进入 Git。

## 常用命令

```powershell
comfy-demo doctor
comfy-demo workflow list
comfy-demo workflow show anima.standard.v1
comfy-demo workflow validate --all
comfy-demo run anima.standard.v1 --prompt "masterpiece, anime character portrait"
comfy-demo job show <job-id>
comfy-demo job wait <job-id>
comfy-demo job cancel <job-id>
comfy-demo watch
comfy-demo dsh bundle
comfy-demo dsh verify integrations\dsh\releases\comfyui-demo-dsh-presets-v0.1.0.zip
```

`studio` 和 `showcase export` 在 M5/M6 门禁通过前会明确拒绝，不会偷偷启用未验证实现。

## 工作流

| ID | 模式 | 说明 |
|---|---|---|
| `anima.standard.v1` | txt2img | Anima 标准生成 |
| `anima.hq-2x.v1` | upscale | Anima 生成与 2× 精修 |
| `animagine.standard.v1` | txt2img | Animagine 对照生成 |
| `larkie.img2img.v1` | img2img | 拉琪图生图身份保持 |
| `larkie.incontext.v1` | incontext | 拉琪 in-context 身份保持 |

工作流注册和哈希见 `workflows/registry.json`；12 条画布原始工作流的只读基线见 `workflows/source_manifest.json`。

## 热文件夹

把符合 `GenerationRequest` 的 JSON 放到 `inbox/pending/`。监听器会迁移到 processing，成功后放到 done；失败后原请求放到 failed，并生成 `.error.json`。不存在绕过统一 schema 的 JSON 快捷路径。

示例：

```json
{
  "workflow_id": "anima.standard.v1",
  "prompt": "masterpiece, original anime character",
  "seed": 0,
  "count": 1,
  "width": 1024,
  "height": 1536,
  "client": "inbox"
}
```

## 文档

- DSH 当前交接入口：`docs/M5_DSH_HANDOFF.md`
- M5 在线验收：`docs/M5_LIVE_ACCEPTANCE_RUNBOOK.md`

- `ENGINEERING_UPGRADE_PLAN.md`：工程总方案。
- `DSH_IMPLEMENTATION_PLAN.md`：DSH 阶段化执行清单。
- `integrations/codex/RUNBOOK.md`：Codex 官方 comfy-mcp 流程。
- `docs/COMFYUI_UPDATE_RUNBOOK.md`：避免 DLL 占用的更新流程。
- `task_plan.md`、`findings.md`、`progress.md`：实施记录。
