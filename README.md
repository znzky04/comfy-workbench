# ComfyUI Agent Studio

一个本地优先、可追溯的 ComfyUI 多入口控制工程。Codex、DSH、CLI、热文件夹和星夜网页工作台共享同一份版本化注册表、参数校验、任务状态与输出规则。

**状态：v0.1 公开准备中，仓库目前仍私有。** 自有代码及作者确认的自有工作流采用 [MIT](LICENSE)；模型、第三方组件和图片不随仓库分发，见 [归属与许可边界](THIRD_PARTY_NOTICES.md)。无需演示视频。

## 先离线试用（无需 GPU / ComfyUI / 模型）

支持从源码仓库安装；暂不提供 PyPI、桌面安装包或脱离源码目录的 wheel 发行。
Python 3.11+；以下为 PowerShell，macOS/Linux 使用 `.venv/bin/python` 与相应激活方式。

```powershell
git clone https://github.com/znzky04/comfyui-agent-studio.git
cd comfyui-agent-studio
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "hatchling>=1.27" "editables>=0.5"
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e ".[web,dev]"
.\.venv\Scripts\python.exe examples/offline_review.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts examples
.\.venv\Scripts\comfy-demo.exe workflow validate --all
```

私有期间克隆仍需要访问权限。常规测试与示例不连接 ComfyUI，不需要作者的画布、参考图或本机目录。离线检查与 GPU 验收分开；本轮未重新生图。[CI 四环境](https://github.com/znzky04/comfyui-agent-studio/actions/runs/40291884948)已实际通过：Windows/Linux × Python 3.11/3.13，每个环境包含 43 项测试、Ruff、离线示例和工作流静态校验；这不代表跨平台 GPU 验收。

## 连接你自己的 ComfyUI

复制 `config.example.toml` 为被 Git 忽略的 `config.local.toml`，填写实际的工作区、input、output 和模型目录。Desktop 的共享图库可能不在工作区内，必须使用它实际配置的路径。相对路径统一以仓库为基准。模板中的 `../ComfyUI` 只是示例，不会创建或启动实例。

配置优先级：模板 → 指定配置文件（或默认本机配置）→ 环境覆盖。可以用 `COMFY_DEMO_CONFIG` 选择配置；环境覆盖包括 `COMFY_DEMO_COMFYUI_URL`、`COMFY_DEMO_WORKSPACE`、`COMFY_DEMO_OUTPUT_ROOT`、`COMFY_DEMO_WEB_HOST`、`COMFY_DEMO_WEB_PORT`。

手动准备 `workflows/registry.json` 声明的模型与节点并核对各自许可。项目不会自动下载；未安装参考节点的用户可先使用与环境匹配的文生图工作流。然后自行启动 Desktop，运行 `comfy-demo doctor`，检查配置、依赖与连接后再使用 `comfy-demo studio`。

## 已知限制

- Windows Desktop 是已有 GPU 验收环境；Linux 离线 CI 不等于 Linux GPU 支持证明。
- DSH v0.1.2 参数契约已验，UI 重导入待验收；DSH 的项目 manifest 需要 Agent 补录。
- 拉琪 in-context 是实验功能：技术运行成功，身份、服装与星环仍未通过视觉验收；完整自有参考节点不随库提供。
- Web 仅限本机单用户；SSE 提供任务阶段，不是逐采样步百分比。见 [安全边界](SECURITY.md)。
- 多图逐个提交；已收到的任务 ID 与参数立即保存。提交失败会继续观察已接受任务并最终标记批次失败；提交中进程退出则保留可查询任务，等待观察超时，不自动补交。远端接受请求到本地收到并保存响应之间仍有不可消除的崩溃窗口，不能保证恰好一次提交。
- `showcase export` 为明确禁用的兼容占位，不是可用的导出功能。
- `legacy` 的 Python 和批处理入口已禁用；只供历史阅读。原始图片与画布文件均保留。

发布准备与验证证据见 [PUBLIC_RELEASE_READINESS.md](docs/PUBLIC_RELEASE_READINESS.md)。

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

本地网页依赖单独安装，项目当前环境已安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web,dev]"
```

本节 E 盘路径是维护者的历史安装记录；新用户按上面的通用快速开始配置自己的目录。本机配置不会进入 Git。

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
comfy-demo studio
comfy-demo dsh bundle
comfy-demo dsh verify integrations\dsh\releases\comfyui-demo-dsh-presets-v0.1.2.zip
```

运行 `comfy-demo studio` 后打开 `http://127.0.0.1:8199`。旧的 `启动画图台.bat` 同样可用。上传、SSE 状态、取消、历史、角色分类和原图详情均使用统一核心；工作台关闭后，ComfyUI 中的任务继续执行，下次启动会恢复状态观察。

个人网站已完成本地集成：新增第 5 张项目卡、`/projects/comfyui-agent-studio` 详情路由与已批准的海梦样例，网站尚未部署。工作台展示图由实际前端离线呈现并明确标注，不作为新的真实生成验收。

`benchmarks/public-selection.json` 当前仅批准海梦 HQ 任务 `e4265b17-a226-4680-90ca-cab1f792137a` 的唯一输出；其他结果不公开。`showcase export` 命令仍是锁定占位，不会自动复制图库。本轮网站只导出批准图的无嵌入元数据 WebP。

## 源码审阅与最小离线示例

源码仓库为私有的 [znzky04/comfyui-agent-studio](https://github.com/znzky04/comfyui-agent-studio)，需要仓库访问权限。网站只链接该仓库，不提供公开源码下载。此前制作的精简审阅包保留为本地文件，不随网站发布；说明见 [docs/review/README.md](docs/review/README.md)。

已安装依赖的本地工程可以直接执行：

```powershell
.\.venv\Scripts\python.exe examples/offline_review.py
```

该示例不联网、不提交生图、不要求模型。它在 `runs/offline-review` 下临时创建独立的示例工作流和 JSON，演示参数绑定、seed 0、记录重载和哈希漂移检测，退出时清理自己的临时目录。真实任务恢复仍以现有服务测试与实际生图验收分别验证。

两个工程决策案例及证据见 [docs/ENGINEERING_DECISIONS.md](docs/ENGINEERING_DECISIONS.md)。

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
- 本地工作台使用与验收：`docs/M6_LOCAL_STUDIO.md`
- 网站当前集成、素材审批与验证：`docs/PERSONAL_WEBSITE_HANDOFF.md`
- 工程决策与个人贡献：`docs/ENGINEERING_DECISIONS.md`

- `ENGINEERING_UPGRADE_PLAN.md`：工程总方案。
- `DSH_IMPLEMENTATION_PLAN.md`：DSH 阶段化执行清单。
- `integrations/codex/RUNBOOK.md`：Codex 官方 comfy-mcp 流程。
- `docs/COMFYUI_UPDATE_RUNBOOK.md`：避免 DLL 占用的更新流程。
- `task_plan.md`、`findings.md`、`progress.md`：实施记录。
