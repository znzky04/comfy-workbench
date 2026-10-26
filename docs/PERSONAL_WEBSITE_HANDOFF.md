# ComfyUI Agent Studio：个人网站交接说明

> 更新：2026-10-26。交给负责个人网站的 Codex 对话阅读。
> 本文记录网站集成的事实与范围；最新状态见下方更新。部署仍需用户明确授权。

## 当前状态（2026-10-26 更新）

- 网站第 5 张项目卡及 `/projects/comfyui-agent-studio` 已在本地实现，lint、build 与桌面/手机验证通过；未部署。网站与工程分别保存 Git 提交，不将网站改动推送到公开远程或触发部署。
- 用户确认工作台界面，并在否决海洋星象祭司与三张替代候选后选定海梦。审批清单仅含任务 `e4265b17-a226-4680-90ca-cab1f792137a` 的唯一输出 `00001`，不能据此公开其他图片。
- 网站实际使用 `marin-hq-v1.webp` 和 `workbench-marin-offline-v1.webp`，位于 `public/images/projects/comfyui-agent-studio/`。前者为原图重新编码、去除嵌入元数据；后者由现有工作台前端离线呈现批准样例，状态与图注明确说明离线展示，不是本轮真实生图截图。E 盘原图保持不变。
- 同人评测独立展示，附 AI 生成、非商业技术评测、权利归属与无隶属背书说明。
- 用户选择补充技术决策案例、可审阅源码和文档同步，不制作演示视频。随后用户要求提交 Git，并先建立私有仓库：https://github.com/znzky04/comfyui-agent-studio 。网站源码入口改为明确标注需权限的仓库链接；原审阅包和源码文本移出网站 public，保留在本地忽略目录，不随网站构建。
- 原始工程与浏览器验收事实仍按下文注明的日期理解。下文列出的未采用候选不代表已经获得公开批准。

## 1. 这次要做什么

在现有个人网站的项目区新增一张 **ComfyUI Agent Studio / 星夜绘图室** 项目卡，点击进入独立工程作品集详情页：

```text
现有项目区 → 新项目卡 → /projects/comfyui-agent-studio
```

页面展示一个可运行的本地 AI 生图工程：多入口连接 ComfyUI、共享版本化工作流、参数校验、任务追踪、输出保留和本地工作台。图片用于证明实际运行与比较质量，工程能力是主线。

这是一份面向访客、招聘者与技术面试的项目案例。公开站点不连接访客电脑的 localhost，不开放 GPU 生图，不嵌入本地工作台，也不提供公网控制 ComfyUI 的接口。

用户已在接手对话中授权本地实施并确认上方列出的素材；其他图片与包含图库的截图仍需先审阅并经用户批准。不要把本地“已生成”误认为“可公开”。

## 2. 两个仓库与现状

### 生图工程（事实来源）

```text
E:\AI\Deepseek\comfyui-demo
```

- 工作流、参数映射、技能包和工程文档以该版本库为准。
- 交接核对时 HEAD：`73d104c`（提示词保存与复制）；之前 `8ab147d` 完成本地工作台。
- 2026-10-26 核对时该仓库无已有未提交改动；本文是随后新增文档。
- 入口：CLI、热文件夹、Codex 官方 MCP、DSH 插件、本地网页。共享核心；各集成的自动化程度见限制说明。
- 本地网页：`http://127.0.0.1:8199/`。是否正在运行需重新检查；截屏不是启动服务的授权。
- 启动器：`E:\AI\Deepseek\comfyui-demo\启动画图台.bat`。
- ComfyUI Desktop 由用户手动管理。任何脚本和 Agent 都不得启动、强杀或更新它。

### 个人网站（实施目标）

```text
D:\VibeCoding\Personal web\v2
```

2026-10-26 只读核对：

- 分支：`codex/larkie-web-pet`。
- `git status --short`：`?? scripts/`；必须保留，不覆盖、不删除、不擅自加入提交。
- `src/content/projects.ts` 当前包含 4 个项目。
- 已有 React、TypeScript、Vite、React Router；复用网站已有组件、路由和视觉体系。
- `npm run lint` 使用 oxlint；`npm run build` 执行 TypeScript 与 Vite 构建；已有 Playwright 依赖。

以上是交接快照，实施前重新检查 Git 状态、适用 AGENTS.md 与页面结构，不假设仍然完全相同。

## 3. 可公开表述的成果与边界

| 内容 | 已有证据 | 文案边界 |
| --- | --- | --- |
| 统一核心 | Python、Pydantic、HTTPX、Typer，配置、注册表、校验、任务 manifest | 不写成自研生成模型 |
| 多客户端 | CLI/热文件夹、Codex 官方 comfy-mcp、DSH 官方插件、本地 Web | 不暗示自行开发了官方插件 |
| 工作流管理 | 5 条 API 工作流有注册与哈希；12 条原始画布工作流保留哈希基线 | 12 条原始画布没有全部转换或全部真实验收 |
| 真实验收 | 8 个正式角色任务有完成图和评估，覆盖 5 条工作流；DSH 与 Codex 均有真实成功记录 | 工程成功与视觉通过分开，不能写“8 张全部满意” |
| 本地工作台 | FastAPI、Jinja、原生 JS、SSE，多图画廊、上传、历史、取消、参数与提示词复制 | SSE 为任务阶段状态，没有逐采样步数字百分比 |
| 可追溯 | 项目任务保存工作流版本/哈希、prompt、参数、seed、参考图哈希、输出路径及错误 | 不承诺跨硬件、模型版本逐像素复现 |
| 图片保留 | 单一 E 盘图库，失败与未采用结果保留，无自动删除接口 | 不把零删除写成内容审核机制 |
| 测试 | 2026-10-26 全套 pytest：33 passed、1 warning | 浏览器验收来自此前记录，别伪称本轮重跑 |

最新测试警告是 Starlette TestClient 的 httpx 弃用提示，不影响本次 33 项通过。此前桌面 1440px、手机 390px 的 Chrome/Playwright 验收通过，包含上传、筛选、弹窗、无横向溢出、减少动画偏好和零 JS 错误；真实网页双图测试验证 seed 0/1、两张不同输出与完成状态。

仍需如实记录：

- DSH v0.1.2 的输出前缀参数已通过官方插件函数验证；该新版预设的 UI 重导入尚未执行。不能声称 v0.1.2 已经全部 UI 验收。
- DSH 插件自身不写项目 manifest，需要 Agent 补录，不是所有插件调用天然自动追溯。
- 拉琪 in-context 经兼容修复可实际运行，但身份、服装和星环还原未通过视觉验收。
- 生成质量有变化；曾有历史异常与视觉失败，已保留证据。
- 部分旧记录未单独保存实际默认负面词，UI 明确提示未知，不按当前默认值补造历史。
- 未核对公开代码仓库地址，不得编造 GitHub 链接；没有公开地址就省略按钮。
- 可以说明“借助 Codex / DSH 完成工程实现与验证”，不夸大为纯手写或自行训练基础模型。

## 4. 五条工作流如何介绍

| ID | 面向访客的解释 |
| --- | --- |
| `anima.standard.v1` | Anima 文字生图，常规生成路径 |
| `anima.hq-2x.v1` | Anima 从文字生成后进行 2× 精修；不是对图库任意历史图点击超分 |
| `animagine.standard.v1` | Animagine 文字生图，用于比较模型表现与标签式提示词 |
| `larkie.img2img.v1` | 原创角色参考图驱动的图生图身份保持测试 |
| `larkie.incontext.v1` | 参考上下文驱动的身份保持实验，保留当前视觉限制 |

访客页可以用可读名称，技术表中保留 ID。不要向访客展示大量节点 ID 或本机路径。

## 5. 推荐页面内容与文案起点

项目卡建议：

```text
标题：ComfyUI Agent Studio
副标题：星夜绘图室 · 本地 AI 生图工作台
摘要：把 Codex、DSH、命令行与网页接入同一套 ComfyUI 工作流，让生成任务有版本、有记录、可比较。
亮点：5 条工作流 · 8 个角色任务 · 33 项自动化测试
标签：Python / ComfyUI / MCP / FastAPI / Workflow
入口：查看项目
```

详情页建议按以下叙事组织，结合现有网站风格调整密度，不要求把每项做成独立大屏：

1. 中英文摘要、项目定位、工作台截图（待批准）。
2. 问题：Agent 与脚本各存工作流会漂移，生图参数和结果难追溯。
3. 方案：统一注册表与任务核心，多个客户端连接用户管理的 Desktop。
4. 架构与一次任务生命周期：请求 → 校验 → 提交 → 状态 → 原图与 manifest。
5. 5 条工作流及 Codex/DSH 两条使用路径。
6. 结果：其他原创角色优先，拉琪身份保持对比，其次独立的动漫角色评测区。
7. 可复现记录、测试与失败案例；指出现有局限与下一步。
8. 技术栈、本人承担的集成工作与上游组件归属。

示例英文摘要：

> A local ComfyUI workbench that connects AI agents, command-line tools and a browser interface through versioned workflows, validated requests and traceable generation records.

视觉沿用个人网站 ZNZSKYLARK / LARKHESIA 的风格。月白、幽蓝、金色可作项目识别元素，不复制整套本地工具 UI，不顺带重新设计首页。

## 6. 素材位置与选图规则

### 原始工作台截图（历史候选，含已弃用旧 B；当前网站不使用这些文件）

```text
E:\AI\Deepseek\comfyui-demo\runs\browser-check\28143f5cb297\desktop-viewport.png
E:\AI\Deepseek\comfyui-demo\runs\browser-check\28143f5cb297\desktop.png
E:\AI\Deepseek\comfyui-demo\runs\browser-check\28143f5cb297\mobile.png
```

截图可能包含图库、暴露服装、失败卡片或本机信息，必须先查看。需要时制作经过审阅的裁剪/脱敏版本，保留原文件；不要直接复制整个图库作为网页素材。

### 原图与任务记录

```text
权威图库：E:\Comfy-Desktop\ComfyUI-Shared\output\comfyui-demo
历史 DSH 图也在：E:\Comfy-Desktop\ComfyUI-Shared\output
任务记录：E:\AI\Deepseek\comfyui-demo\runs\YYYY\MM\<job-id>.json
评测清单：E:\AI\Deepseek\comfyui-demo\benchmarks\characters.json
公开审批：E:\AI\Deepseek\comfyui-demo\benchmarks\public-selection.json
```

当前 `approved_job_ids` 仅包含海梦 HQ 任务 `e4265b17-a226-4680-90ca-cab1f792137a`，其唯一输出为 `00001`。不能自行批准其他任务，也不能把未经批准的原图加入网站 public 或 Git。批准必须明确到图片；同一任务有多张时也要说明选哪张。任何网站复制仅针对批准的精选，不移动、不删除原图。

正式评测共 2 拉琪、3 热门角色、3 其他原创。以下 job ID 可用于从 manifest 定位，不需要接手者遍历整盘：

| 角色 / 内容 | job ID | 建议 |
| --- | --- | --- |
| 原创海洋星象祭司 HQ | `8e70b402-8ac3-4dd5-8825-4c1cd7fdbb4c` | 优先向用户展示的候选，尚未获批 |
| 原创蒸汽朋克工匠 | `b4ee7f3e-0b09-4313-9fbd-8c4d05f54572` | 有服装与构图偏差，先审阅 |
| 原创赛博剑士 | `f4f95362-658d-45cb-9584-9869a0aba99c` | 发长、肤色偏离 brief，适合说明限制 |
| 拉琪 img2img | `67abc395-1dc9-4687-8757-253f82420c96` | 参考身份保持较强，服装先审阅 |
| 拉琪 in-context | `ae92c6ea-f306-4ed7-ad96-38834ff1bd6f` | 技术成功、视觉不合格，不默认作主视觉 |
| 时崎狂三（DSH） | `31ea2ca0-699f-4629-ab25-fe3dd4f70050` | 只用于明确标注的同人评测区 |
| 芙莉莲（纠正性复测） | `f8234a7f-45c9-4194-bfe4-ae39f9c11534` | 同上；首次抽象失败图另存 |
| 喜多川海梦 HQ | `e4265b17-a226-4680-90ca-cab1f792137a` | 同上 |

原计划希望公开展示 8 个任务，随后用户选择公开图片稍后选。最新仅批准上方列出的海梦输出；不能用原计划代替其他图片的逐张批准，也不为凑数量公开低质量或不合适的结果。

公开资产仅导出必要的图像与明确批准的参数。移除本机绝对路径、用户名、参考图路径、私人 prompt、未批准参考图与 PNG 内嵌工作流元数据；公开 JSON 不得直接照搬完整 manifest。图片可生成适量 WebP/缩略图，不覆盖原始 PNG，不做整图下载包。

若包含热门动漫角色，独立区域显示：

```text
Fan Character Benchmark / 非商业同人技术评测
角色及原作权利归各自权利人所有。
本站图片为本地生成模型的技术测试结果，与原作者、动画制作方及版权方无隶属或背书关系。
```

明确 AI 生成属性；不使用官方截图、海报、Logo，不暗示官方合作，不把同人当成主要原创作品，不提供热门角色图片下载包。模型与输出授权如需具体陈述，另行核实，不能宣称“原创角色即可保证完全没有权利负担”。

## 7. 网站实施范围

- 修改 `D:\VibeCoding\Personal web\v2\src\content\projects.ts` 增加项目记录。
- 在现有路由机制内增加 `/projects/comfyui-agent-studio` 与独立详情组件。
- 项目卡增加详情入口，保留另外 4 个项目内容。
- 新增项目专属素材目录，只放批准的衍生资产。
- 若内容契约/测试写死 4 个项目，定位后改为 5；不要未经检查就全局替换数字。
- 允许必要的项目卡类型/样式局部改动，复用现有公共组件，确保已有项目卡正常。
- 不改其他职业事实，不重构首页、笔记、Supabase、音频、搜索或拉琪桌宠。
- 不开启公网生图服务，不暴露 8188/8199，不加入 API 密钥，不部署 Vercel。
- 不改生图核心、工作流或 ComfyUI 安装，不重新生成图片来补素材，除非用户另有要求。

## 8. 交付与验收

实施前：读网站适用指令、检查 Git 状态，确认现有卡片与路由实现。先保全工作区，再增量修改。

交付时至少验证：

```powershell
cd 'D:\VibeCoding\Personal web\v2'
npm run lint
npm run build
```

使用已有 Playwright 验证桌面与手机：新增卡片与入口、详情路由直接打开及刷新、返回导航、图片比例/加载、无横向溢出、键盘可达、减少动画偏好；热门角色声明在相应区域清晰可见。检查原首页、其他项目卡、笔记、搜索、音频、桌宠的关键交互。先核对预览服务和历史脚本，避免覆盖未跟踪 `scripts/`。

报告修改文件、实际测试结果、预览地址、素材审批状态及未完成项。截图/人工评分不得包装成自动化指标。实际部署等待用户明确授权。

## 9. 需要更多事实时先读这些

以下均相对 `E:\AI\Deepseek\comfyui-demo`：

1. `docs/M6_LOCAL_STUDIO.md`：工作台功能、测试与限制。
2. `docs/M5_ACCEPTANCE_REPORT.md`：真实生成与 DSH 限制。
3. `README.md`、`workflows/registry.json`：架构与实际工作流。
4. `benchmarks/characters.json`、对应任务 manifest：参数与评测。
5. `ENGINEERING_UPGRADE_PLAN.md`：总方案，实施阶段旧状态以最新验收和用户指令为准。

无需复制整个生图对话。遇到材料缺失，报告具体文件或审批缺口；不要编造生成结果、素材许可或上线状态。
