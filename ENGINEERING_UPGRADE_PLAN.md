# ComfyUI Agent Studio v2 工程升级计划

## 1. 目标与边界

将 `comfyui-demo` 升级为作品集级本地生图工程，由版本库统一管理工作流、参数、任务记录、集成包和文档，同时服务 Codex、DSH、CLI、热文件夹与本地网页。

固定决策：

- ComfyUI Desktop 由用户手动启动、停止和更新；任何项目入口都只能连接。
- Codex 使用官方 `comfy-mcp`，DSH 使用官方 `dsh-comfyui 0.5.x`。
- 第一轮正式支持 5 条 API 工作流；12 条原始画布工作流仅登记、校验和保护。
- ComfyUI 的 E 盘输出目录是唯一图片图库；项目不保存重复副本，不自动删除任何成功图或失败图。
- DSH 通过版本化 preset v1 ZIP 导入，不修改插件源码、`node_modules` 或私有数据库。
- 实施顺序严格为核心、CLI/热文件夹、DSH/Codex、真实生成、本地网页、个人网站。
- 角色评测固定为 2 次拉琪、3 次热门动漫角色、3 次其他原创角色。

## 2. 目标架构

```text
用户手动管理 ComfyUI Desktop (127.0.0.1:8188)
                         │
       comfyui-demo 统一工程核心
  配置 / 注册表 / 校验 / 任务 / manifest
        ┌────────┬────────┬────────┐
   Codex MCP    DSH     CLI/热文件夹    本地网页
        └────────┴────────┴────────┘
                         │
              ComfyUI 单一输出图库
                         │
                 人工批准的安全导出
                         │
               ZNZSKYLARK 项目详情页
```

## 3. 公共契约

### 3.1 配置

`config.example.toml` 是可提交模板；`config.local.toml` 是 Git 忽略的本机覆盖。配置包括 ComfyUI URL、连接和任务超时、工作区、工作流、manifest 与权威输出路径、日志轮转、磁盘阈值及 Web 监听地址。

### 3.2 工作流注册

每条正式工作流必须记录稳定 ID、版本、API JSON、SHA-256、模式、语义参数到节点输入的映射、约束、模型/LoRA/upscaler/自定义节点需求、输出节点、命名规则和 DSH 元数据。

正式工作流：

1. `anima.standard.v1`
2. `anima.hq-2x.v1`
3. `animagine.standard.v1`
4. `larkie.img2img.v1`
5. `larkie.incontext.v1`

`legacy.main-anima.v1` 只作为历史来源登记，不作为运行时隐藏依赖。

### 3.3 请求和任务

统一请求字段为 `workflow_id`、`prompt`、可选 negative prompt、seed、count、尺寸、steps、CFG、denoise、输入图片、输出标签和客户端来源。`seed=0` 必须保留；只有缺省或 `-1` 代表随机。未知参数必须拒绝。

状态机为：

```text
created → submitted → queued → running
                         ├→ completed
                         ├→ failed
                         └→ cancelled
```

任务 manifest 保存到 `runs/YYYY/MM/<job-id>.json`，记录工作流版本和哈希、原始与解析参数、模型、LoRA、输入图片哈希、时间、输出绝对路径及错误。

### 3.4 图片规则

权威前缀为：

```text
E:/Comfy-Desktop/ComfyUI-Shared/output/comfyui-demo/YYYY-MM-DD/<workflow-id>/<job-id>_<seed>_<index>.png
```

所有入口返回权威绝对路径；不覆盖、不复制、不自动删除。公开网站只能复制人工批准、经过脱敏检查的精选图片。

## 4. 里程碑

### M0 文档、基线和回滚

- 保存总方案与 DSH 执行版。
- 记录磁盘余量、5 条 API 和 12 条画布工作流哈希。
- 导出 DSH 当前“主Anima”预设备份。
- 初始化 Git，忽略模型、图片、日志、运行记录、本机配置和缓存。
- 建立 `task_plan.md`、`findings.md`、`progress.md`。

### M1 统一核心与生命周期

- 建立 E 盘 `.venv` 和 Python 包。
- 使用 Pydantic、HTTPX、Typer 实现配置、请求校验、`ComfyClient` 和 `doctor`。
- 完成健康检查、系统状态、校验、上传、提交、查询、等待、取消与输出解析。
- 移除所有自动启动或强杀 ComfyUI 的调用；未运行时快速失败并提示打开 Desktop。
- 写明更新流程：退出 Desktop、确认 8188 释放且无 `main.py`、更新、重启、复验。

### M2 注册表与运行记录

- 迁入 5 条 API 工作流并建立 schema/注册表。
- 建立 12 条画布工作流只读清单。
- 从 Python 运行逻辑移除硬编码节点 ID。
- 修复 JSON 热文件绕过校验、`seed=0`、多图覆盖和错误不可见。
- 实现原子写入的运行 manifest。

### M3 CLI、热文件夹和兼容层

- 提供 `doctor`、`workflow`、`run`、`job`、`watch`、`studio`、`dsh` 和 `showcase` 命令。
- 热文件夹采用 pending/processing/done/failed；失败保留原文件并生成 `.error.json`。
- 旧 Python 和 bat 入口转调新 CLI，保留迁移提示。

### M4 DSH 与 Codex

- 构建 `dsh-comfyui-workflow-preset` v1 ZIP，包含 5 条工作流、参数、标签和技能包。
- 导入新版本前保留旧预设；测试通过后仅标记旧版 deprecated。
- Codex 固定流程：server info → system stats → validate → async run → job → output paths。
- 两端使用完全相同的工作流 SHA-256；任何失败不修改主工作流。

### M5 真实生成验收

共执行 8 个正式任务：

- 拉琪：img2img 与 in-context 各一次，检查月白发、少量香槟金挑染、幽蓝羽翼、简洁金色星环及成熟日漫少女形态。
- 热门角色：时崎狂三、芙莉莲、喜多川海梦各一次。
- 原创角色：赤铜短发机械义肢蒸汽朋克工匠、墨蓝长发赛博夜行剑士、青绿色波浪长发海洋星象祭司各一次。

8 次任务覆盖全部 5 条工作流，并至少各有一次由 DSH 和 Codex 提交。记录参数、seed、模型、参考图哈希、绝对输出路径及人工评分。任何未通过视觉验收的图片仍然保留。

### M6 本地网页

只有 M5 通过后开始。技术栈为 FastAPI、Pydantic、Jinja、原生 JavaScript、SSE、CSS 动画和 Uvicorn，只监听 `127.0.0.1:8199`。网页只能调用统一核心，不能形成第二套工作流或队列实现。

功能包括连接/显存、工作流选择、提示词和参数、参考图上传、队列/进度/取消/错误、历史、多图画廊、manifest 路径、评测筛选及 DSH/Codex 说明。视觉采用月白、幽蓝、金色和星夜主题，并支持移动端与 reduced motion。

### M7 个人网站

只有 M6 通过后修改 `D:\VibeCoding\Personal web\v2`：新增第五个项目记录、`/projects/comfyui-agent-studio` 路由、独立详情页与项目资产，并将内容契约从四个项目更新为五个。保护现有分支和未跟踪 `scripts/`，不重构其他页面，不发布 Vercel。

热门角色区域必须明确标注“Fan Character Benchmark / 非商业同人技术评测”，说明 AI 生成、无隶属或背书关系及权利归属；不得使用官方截图、Logo 或提供下载包。

## 5. 测试与完成条件

- 单元测试覆盖配置覆盖、注册表、参数映射、seed 0、边界、输入图、防覆盖命名、状态机、原子 manifest、热文件恢复、DSH ZIP 和公开导出。
- 合约测试覆盖 5 条 API、节点输入、依赖、12 条原始哈希、preset v1、Codex runbook 与 2+3+3 评测清单。
- 在线测试覆盖服务未启动、提交/队列/运行/完成/失败/取消/超时、单图/多图/超分、5 条真实工作流及双 Agent。
- 网站执行 lint、build、桌面/移动 Playwright 和原有功能回归。

工程完成要求：5 条工作流真实运行；所有入口不管理 ComfyUI 进程；图片零自动删除、零静默覆盖；每次运行有 manifest；DSH 包可导入回滚；8 个角色任务均有结果和评估；网页与个人网站通过各自门禁。

## 6. 禁止事项

- 禁止项目启动、强杀或更新 ComfyUI。
- 禁止修改 12 个原始画布工作流。
- 禁止删除、移动或覆盖任何既有或新生成图片。
- 禁止直接修改 DSH 私有数据库、`workflows.json` 或 `node_modules`。
- 禁止 M5 前开发网页、M6 前修改个人网站。
- 禁止未经授权发布网站、下载模型/节点或调用付费 API。
