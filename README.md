# Comfy Workbench · 星夜绘图室

让现有的 ComfyUI 工作流通过网页、命令行和 AI Agent 使用，并把每次生成的提示词、参数、版本与结果留成可追溯的记录。

## 为什么做这个项目？

这个项目最初想解决一个实际需求：**通过 Codex 和 DSH 对话，操作本地 ComfyUI 生成图片，并让同样的工作流也能在自己日常使用的网页和脚本中运行。**

直接把这些入口拼在一起，很容易遇到几个问题：不同入口各存一份工作流，修改之后版本对不上；参数散落在脚本或对话里，生成后很难找到对应的 prompt、seed 和参考图；失败任务只剩一条报错，部分成功结果没被记录；额外的后台启动脚本还可能占用 ComfyUI，影响 Desktop 更新。

Comfy Workbench 围绕这些问题整理了一套共同约定：以仓库中的工作流注册表为来源，统一参数校验、任务记录和图片路径，连接用户自己管理的 ComfyUI。网页、CLI 和热文件夹直接使用同一个 Python 核心；Codex 和 DSH 则通过官方工具、预设包及操作说明接入这些约定。

项目的工作重点是**把本地生图流程做成可使用、可检查、可扩展的工具**。生成模型、ComfyUI 本身、官方 MCP 和 DSH 插件均为上游能力，个人贡献是工作流集成、参数与任务管理、本地工作台和验证，开发过程借助了 Codex / DSH。

## 做完之后能用来干什么？

- **日常生图**：在网页中选择已注册工作流，填写提示词，设置尺寸、张数和 seed；需要参考图的链路可上传自己的图片。
- **查看结果**：观察排队、运行、完成、失败或取消状态，在本地画廊查看多张输出、原图位置和错误信息。
- **回看一次生成**：查看并复制正向/负面提示词，追查实际参数、模型与 LoRA 名称、工作流版本/哈希、参考图哈希和输出文件。
- **脚本化使用**：通过 CLI 或热文件夹提交请求；开发者可扩展注册表和参数映射，接入自己的工作流。
- **与 Agent 配合**：按 runbook 使用 Codex 官方 comfy-mcp 或 DSH 插件，使用项目管理的 API 图、预设和操作说明。插件另行安装配置，DSH 的项目任务记录需要 Agent 补录。

例如，想比较同一角色在两个工作流下的表现，可以分别提交任务，再从记录中核对提示词、seed 和结果；某次失败也保留任务与已有输出，方便诊断。保存这些信息用于追溯和对照，不承诺跨硬件、模型版本的像素级复现。

```text
用户自行管理的 ComfyUI Desktop
             ↑ HTTP 连接
    工作流注册 / 校验 / 任务 / 记录
             ↑
       网页 / CLI / 热文件夹

Codex MCP / DSH → 项目工作流、版本化预设与 runbook → ComfyUI
```

图片保存在用户配置的 ComfyUI 图库；项目保存运行记录，不再把图片重复下载到源码目录。

## 适合谁？下载后是什么样？

当前是 **v0.1 测试版，面向已有 ComfyUI 环境的用户和开发者**，需要源码安装和手动配置。

| 你的环境 | 安装后能做什么 | 实际生图还需要什么 |
| --- | --- | --- |
| 有 Python，没有 ComfyUI 或可用 GPU | 运行离线示例和测试；安装网页依赖后可打开工作台，显示未连接和空图库 | 自行准备可运行的 ComfyUI 后端、硬件、模型和节点 |
| 已安装 ComfyUI，但依赖不齐 | 打开工作台、查看参数，用 doctor 查看缺项 | 按所选工作流准备依赖并填写真实路径 |
| 后端、所选工作流依赖和路径均已配置 | 通过网页、CLI 或热文件夹实际生成，查看自己的图片和记录 | Agent 入口需要另外配置相应工具/插件 |

浏览器访问 `http://127.0.0.1:8199` 后，会看到星夜风格的生图表单、工作流选择、预览区与历史图库。新安装从空图库开始，作者电脑上的图片和历史不会出现在你的电脑。

仓库不包含 Python/ComfyUI 安装器、模型权重、参考图、生成图片、运行历史、私人配置或已安装的 Agent 插件，也不会自动下载这些内容。增加新工作流需要维护 API 图、参数映射和哈希；工作台不是任意 JSON 的自动适配器或通用模型管理器。

## 安装与离线试用

需要 Python 3.11+，从源码仓库安装；目前没有 PyPI、桌面安装包或独立 wheel 发行。仓库目前私有，克隆需要访问权限。

PowerShell：

```powershell
git clone https://github.com/znzky04/comfy-workbench.git
cd comfy-workbench
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "hatchling>=1.27" "editables>=0.5"
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e ".[web]"
.\.venv\Scripts\python.exe examples/offline_review.py
```

macOS/Linux 使用 `.venv/bin/python` 等对应路径。离线示例不连接 ComfyUI、不下载模型、不生成图片，演示参数绑定、seed 0、记录重载和哈希漂移检测。

仓库与展示名现为 **Comfy Workbench**；保留 Python 导入名 `comfyui_agent_studio`、已有发行元数据名 `comfyui-agent-studio` 和 CLI `comfy-demo`，方便原有脚本继续使用。现有本机目录和图库路径无需因改名而迁移。

## 连接自己的 ComfyUI，生成第一张图

1. 复制 `config.example.toml` 为被 Git 忽略的 `config.local.toml`。填写真实工作区、input、output 和模型目录。Desktop 的共享图库可能不在工作区内；相对路径统一以仓库为基准。
2. 查看 `workflows/registry.json`，准备所选工作流的模型与节点，并核对其许可。首次可从 `anima.standard.v1` 开始，准备它声明的模型和 LoRA。不要直接套用作者机器的目录。
3. 自己打开 ComfyUI Desktop，等待本机 `http://127.0.0.1:8188` 可连接，再执行：

   ```powershell
   .\.venv\Scripts\comfy-demo.exe doctor
   .\.venv\Scripts\comfy-demo.exe studio
   ```

4. 打开 `http://127.0.0.1:8199`，选择 Anima Standard，输入提示词，先生成一张。成功后可在图库查看图片、参数、提示词和原图路径。生成内容不限于拉琪，可以描述其他原创角色或场景，表现取决于模型。

doctor 会报告全部注册工作流的依赖情况；首次运行只需满足自己所选链路的要求。网页在未连接 ComfyUI 时也可以打开，但无法实际生图。

配置优先级为：模板 → 指定配置或默认本机配置 → 环境覆盖。可用 `COMFY_DEMO_CONFIG` 选择配置；环境覆盖字段见 `src/comfyui_agent_studio/config.py`。

## 当前工作流与入口

| 工作流 | 用途 | 额外条件 |
| --- | --- | --- |
| `anima.standard.v1` | Anima 标准文生图 | 注册表中的基础模型与 LoRA |
| `anima.hq-2x.v1` | 从文字生成后进行 2× 精修 | 超分模型与相应节点；不是任意历史图片的超分按钮 |
| `animagine.standard.v1` | Animagine 文生图对照 | 对应模型与标签式提示词 |
| `larkie.img2img.v1` | 参考图重绘、身份保持测试 | 自备一张参考图 |
| `larkie.incontext.v1` | 参考上下文身份保持实验 | 参考图、兼容参考节点与对应 LoRA；完整节点没有随库提供 |

完整私有版登记了上述配置，但新克隆者不能据此假设五条链路都能开箱即用。图生图链路目前只支持一张参考图，多张会明确拒绝。

```powershell
comfy-demo workflow list
comfy-demo workflow show anima.standard.v1
comfy-demo workflow validate --all
comfy-demo run anima.standard.v1 --prompt "An original adult anime character in a moonlit city"
comfy-demo job show <job-id>
comfy-demo job wait <job-id>
comfy-demo job cancel <job-id>
comfy-demo watch
comfy-demo studio
```

CLI 需激活项目虚拟环境，或使用 `.venv\Scripts\comfy-demo.exe` 的完整路径。热文件夹将符合 `GenerationRequest` 的 JSON 放入 `inbox/pending/`，成功归档到 done，失败归档到 failed 并保存错误记录；同名请求不会覆盖旧证据。

Codex 使用说明见 [runbook](integrations/codex/RUNBOOK.md)。DSH 通过版本化 preset v1 ZIP 导入，使用 `comfy-demo dsh bundle` / `dsh verify`；不修改插件源码和私有工作流数据库。

## 图片、记录和运行边界

- 图片写入自己配置的 ComfyUI 图库，记录写入 `runs/YYYY/MM/<job-id>.json`。所有成功、失败、未采用的图片都保留，没有自动删除图片的入口。
- ComfyUI Desktop 始终由用户启动、停止和更新。关闭工作台不会关闭 ComfyUI，已提交的任务可能继续执行。
- Web 只监听本机，是单用户工具；不要通过代理或隧道直接开放到公网。SSE 显示任务阶段，不提供逐采样步百分比。
- 多图逐个提交，已收到的任务 ID 和参数逐个保存。仍存在远端接受请求、本地尚未保存响应的窗口，不能保证恰好一次提交；文件原子替换也不等于跨进程事务。
- 本项目客户端取消使用带 prompt_id 的定向中断，要求后端支持该能力；已有核查环境为 ComfyUI 0.42.x。
- DSH v0.1.2 参数契约已验，UI 重导入仍待验收；拉琪 in-context 技术成功但视觉还原不足，保留为实验链路。
- `showcase export` 是未实现的兼容占位；`legacy` 中的历史启动入口已禁用。

## 验证到了什么程度？

[四环境 CI](https://github.com/znzky04/comfy-workbench/actions/runs/40295864777) 已通过：Windows/Linux × Python 3.11/3.13，每个环境 65 项测试、Ruff、离线示例和工作流静态校验通过。

维护者 Windows Desktop 上完成了 8 个正式角色任务，覆盖 5 条工作流，并分别记录技术结果和视觉不足。Linux 的离线 CI 不等于 Linux GPU 验收；另一台全新电脑从安装到首次生图，尚未作为独立验收完成。

开发检查（先安装开发依赖）：

```powershell
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e ".[web,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts examples
.\.venv\Scripts\comfy-demo.exe workflow validate --all
```

本项目实现的是 ComfyUI 之上的本地工程层；测试通过代表列出的检查通过，不代表所有画面都达到人工审美要求。

## 许可与更多资料

自有工程代码采用 [MIT](LICENSE)。部分工作流来自网上下载，**原作者未知、许可未确认**，这些工作流及来源未确认的派生配置不纳入自有代码的 MIT 授权。完整仓库目前保持私有；未来公开内容需按来源和许可审阅。模型、节点和图片各自的权利不会因工程代码的 MIT 授权改变，见 [第三方说明](THIRD_PARTY_NOTICES.md)。

- [安全边界](SECURITY.md) · [贡献说明](CONTRIBUTING.md)
- [工作台使用与历史验收](docs/M6_LOCAL_STUDIO.md)
- [两个工程决策案例](docs/ENGINEERING_DECISIONS.md)
- [后续工程审查与修复](docs/ENGINEERING_REVIEW_2026-10-26.md)
- [公开准备报告](docs/PUBLIC_RELEASE_READINESS.md)
- [DSH 集成说明](docs/M5_DSH_HANDOFF.md) · [Codex runbook](integrations/codex/RUNBOOK.md)
- [ComfyUI 更新维护流程](docs/COMFYUI_UPDATE_RUNBOOK.md)
- [个人网站交接说明](docs/PERSONAL_WEBSITE_HANDOFF.md)

`ENGINEERING_UPGRADE_PLAN.md`、`DSH_IMPLEMENTATION_PLAN.md` 和实施日志保留早期项目名及历史决策；当前状态以最新报告和本文为准。个人网站另由网站项目维护，不属于生图工作台运行的前提。
