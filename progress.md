# Progress

## 2026-10-26（分仓提交与私有备份）

- 用户要求提交 Git，工程先采用私有仓库。已创建 `znzky04/comfyui-agent-studio`，工程 origin 指向该私有仓库；网站使用独立的 `codex/comfyui-portfolio` 本地分支。
- 网站原有 origin 为公开仓库。为避免改变正式站或触发预览部署，本轮只在网站本地提交，不推送网站远程。
- 页面源码入口改为需权限的 GitHub 私有链接。原网站 public 中的 5 个审阅文件移到本地忽略目录保留，不继续随网站构建分发源码。
- 下方“源码包下载、无远程仓库”等描述为此前实施历史，当前状态以上述私有仓库策略为准。

## 2026-10-26（网站集成与工程展示）

- M7 已完成本地项目卡、独立详情路由、桌面/手机与交互回归验证，未部署、推送或提交网站改动。
- 用户确认工作台界面，否决海洋星象祭司与三张替代候选，最终选定海梦 HQ 的唯一输出；审批清单只包含该任务。原图和未采用图均保留。
- 网站只使用批准图的无嵌入元数据 WebP；工作台展示由既有前端离线呈现海梦，状态与图注明确说明，不冒充新的 GPU 验收。
- 用户选择补充技术决策、可审阅源码与文档同步，不制作演示视频。新增两个有源码和测试证据的决策案例与最小离线示例。
- 工程无远程仓库，当前源码入口采用精简审阅包；不编造 GitHub 地址，不公开生产工作流、模型、图库、运行记录或本机配置。
- 本轮实际重跑工程 pytest：33 passed、1 warning；新增离线示例通过，Ruff 通过。原有工作台浏览器/GPU 验收继续按历史日期记录。
- 已同步 README、M6 当前状态、网站交接与任务表；下方为原始实施历史，过往 M7 暂缓/审批为空的记录不是当前状态。

## 2026-10-25（提示词历史）

- 用户要求保存每次运行的 prompt。核对确认正向词原已保存在 request.prompt，补充详情中的独立正向/负面词文本框与复制按钮。
- 注册表准备阶段改为记录所有实际参数，包含省略时实际使用的默认负面词；旧记录缺失的默认负面词显示为未单独记录，不伪造回填。
- 新增默认负面词、显式空串和自定义负面词的持久化回归测试；不重新生成或删除任何图片。

## 2026-10-25（M6 本地工作台）

- 用户查看最后一张 in-context 后要求继续；工程验收报告已区分技术成功和视觉不足，M6 开始。
- DSH v0.1.2 暴露 output_prefix，官方插件参数处理函数验证 5/5 通过；不修改插件源码或私有数据库。新版 UI 重导入待 DSH 服务打开后执行。
- Web 依赖已安装至项目 E 盘 .venv。浏览器测试包大文件下载超时一次；改为独立安装网页依赖并复用现有浏览器测试环境。
- 完成 FastAPI/Jinja/原生 JS/CSS 星夜工作台：5 工作流、参数、参考图、实时任务、取消、历史、多图画廊与详情；只调用统一服务。
- 浏览器首次上传发现 Shared input 的 Windows 写入权限限制，改由 ComfyUI 自身上传接口写入；multipart 临时文件定向 E 盘，支持完整请求与 chunked 上传大小限制。
- 真实浏览器双图任务 `b8a55d3c-7528-4eab-a7c3-74d7e3db99c2` 成功：512×768、16 steps，seed 0/1，两个权威输出均存在、manifest client=studio，SSE 到达 completed。
- 增加重启恢复、超时、取消幂等和部分图片结果保留；不重提交旧任务，不删除任何图片。
- 最终 pytest 30 passed；Ruff 通过。Playwright 使用现有 Chrome headless，桌面/手机、筛选、详情、上传、CSRF、无横向溢出和零 JS 错误全部通过。最终截图 runs/browser-check/28143f5cb297。
- 用户明确选择“先完成本地工作台，公开图片稍后选”：M7 暂缓，个人网站无修改，public-selection 为空，公开导出继续锁定。

## 2026-10-25（Codex 再接手）

- 阅读 DSH 原始压缩会话、提交 b3daf0b 和交回文档，确认狂三已完成，阻塞在 in-context 容器接口。
- Desktop 关闭期间备份节点为 `incontext.py.bak-codex-containers-20261025-184155`，完成第二层容器兼容修复。
- 新增 `scripts/check_anima_attention_compat.py`：修复前 2 项容器测试复现原故障；修复后 6 项全部通过。运行使用 ComfyUI 自带 torch，不新增依赖。
- 下一步：记录版本化补丁、复核项目测试，然后等待用户手动打开 Desktop，使用官方 comfy-mcp 运行正式拉琪 in-context。
- 版本化容器补丁已保存，反向适用性检查通过；节点最终 SHA-256 为 `ee9b7f3c4d275779ff4717c5bee3024f6e8b6a2deb8d48c4d1a1b8351375e4e3`。
- 最终离线验收：项目 pytest 19 passed，维护范围 Ruff 通过，5/5 注册工作流静态校验通过，注意力专项 6/6 通过。详细恢复/回滚记录见 `docs/ANIMA_ATTENTION_COMPATIBILITY.md`。
- 用户手动打开 Desktop 后，官方 MCP 确认 ComfyUI 0.42.5 在线、约 10.77 GiB 空闲显存；正式 in-context 预检无错误/警告，异步提交并完成，ComfyUI 实际执行 88.02 秒。
- 正式 job `ae92c6ea-f306-4ed7-ad96-38834ff1bd6f`，prompt `a031443e-c606-42dd-98b4-9b7cf9669b14`，seed 240102、832×1216、28 步、CFG 4.5；输出与评分已写入 manifest。
- 图片技术成功但视觉不通过：衣装更暴露、参考服饰与面部身份保持弱、金色星环变成星芒；图已保留且不列入公开精选。评分来自 Codex 视觉检查，不代表用户批准。
- 已复核 8/8 正式任务全部有 completed manifest、实际存在的输出与评分，覆盖 5/5 工作流及 CLI/DSH/Codex；12 个原始画布工作流哈希全部不变。M5 尚有视觉验收和 DSH 输出前缀契约缺口，保持 M6/M7 门禁。

## 2026-10-24

- 读取并采用 `planning-with-files-zh`、`codebase-recon`、`frontend-design`、`webapp-testing` 指引。
- 确认项目尚无规划文件，创建 `task_plan.md`、`findings.md`、`progress.md`。
- 复核 12 个原始画布工作流与 5 个现有 API 工作流仍存在。
- M0 进行中：下一步为磁盘余量、完整基线、方案文档、哈希与 Git 初始化。
- 已确认 E 盘可用空间约 145.91 GB，并记录既有图片目录体积。
- 已完成 5 个 API 工作流与 12 个画布工作流的 SHA-256 基线采集。

## 2026-10-25

- 保存 `ENGINEERING_UPGRADE_PLAN.md` 与 `DSH_IMPLEMENTATION_PLAN.md`。
- 建立 E 盘 `.venv` 并安装核心、测试和格式化依赖；项目以 editable 方式安装。
- 完成统一配置、请求模型、工作流注册、ComfyUI 客户端、任务 manifest、doctor 和生成服务。
- 完成 CLI、四状态热文件夹、旧入口兼容包装；旧源码存入 `legacy/`。
- 完成 DSH preset v1 构建/验证、旧“主Anima”备份、5 个技能包和 Codex runbook。
- 修复本地 HTTP 代理导致的 502/慢失败，Desktop 关闭时 doctor 约 1.4 秒返回且不启动进程。
- 自动验证：pytest 17 passed，ruff 通过，5/5 工作流静态校验通过。
- Git 已初始化，并按 M0、M1、M2、M3、M4 建立 5 个独立提交。
- M0 已完成；M1–M4 离线部分通过。
- 已找到拉琪参考图并核对 SHA-256，补齐 8 个固定请求、参数、客户端分工和 M5 runbook。
- 已实际执行“ComfyUI 未启动”提交测试：命令返回 1，任务 manifest 进入 `failed`，保留 `seed=0`、工作流哈希和错误详情，且没有启动进程或生成/删除图片。
- 通过官方 comfy-cli 将 comfy-mcp 默认工作区从错误的 C 盘目录纠正为 E 盘真实 ComfyUI；`server_info` 已确认，服务仍保持未启动。
- M5 受外部状态阻塞：需要用户手动启动 ComfyUI Desktop；M5 通过前保持 M6/M7 门禁。
- 用户已手动打开 Desktop；在线初检发现两个相同 `main.py` 进程均未监听 8188，且 Desktop 实际使用 E 盘 Shared 输入/输出目录。正在只读检查启动日志，不会结束或重启进程。
- 日志确认两个 PID 是父子进程而非双实例，服务器已进入监听阶段；项目配置、输出路径解析和模型扫描已改为 Desktop 的 E 盘 Shared 目录。
- 官方 comfy-mcp 已确认服务在线、ComfyUI 0.42.3 和约 10.77 GiB 可用显存；M5 进入在线校验阶段。
- 完整 doctor 通过：9 个模型/LoRA/upscaler 和 3 个关键自定义节点均可用，队列为空。
- 官方 comfy-mcp 对 5 条注册工作流逐一预检，全部 `valid=true`、零错误、零警告、无付费节点。
- `anima.standard.v1` 首个真实任务（原创蒸汽朋克工匠）成功，约 30 秒完成，Shared 输出路径和 manifest 正确。
- 首图人工验收：机械臂、赤铜短发和工坊材质清晰；不足是未完整全身、服装比非性化目标更暴露。图片保留并补录评分字段。
- `animagine.standard.v1` 首次真实任务（芙莉莲）技术完成但视觉失败：没有人物，仅有金色对称抽象图形。原图保留，下一步改为检查工作流链路而非重复生成。
- Animagine 诊断完成：模型、VAE、节点连接、采样器和 PNG 内嵌参数均正常；对照官方模型卡后，将两条 Animagine 评测 prompt 改为标签式结构并把质量标签移到末尾，芙莉莲纠正性复测使用新 seed `240212`。
- Animagine 芙莉莲纠正性复测和原创赛博剑士均成功并评分；首次抽象失败图保留。
- 拉琪 img2img 成功并评分；身份保持强，但深色背景和非性化提示遵循不足。
- 海梦与海洋星象祭司两条 HQ 2× 任务串行成功并评分，没有显存错误。
- 拉琪 in-context 通过官方 comfy-mcp 完成上传、预检和提交，但因自定义节点不兼容 ComfyUI 0.42.3 的 `preferred_attention` 在采样阶段失败，manifest 已进入 failed；未进行无改动重试。
- 官方 comfy-mcp 随后成功完成 Anima 标准烟雾测试，输出 `E:\Comfy-Desktop\ComfyUI-Shared\output\anima_00002_.png`，证明 MCP 主链路正常。
- 已形成 `docs/M5_DSH_HANDOFF.md` 和版本化兼容补丁；下一步交给 DSH 导入预设、运行狂三并在用户手动关闭/重开 Desktop 的配合下处理兼容问题。M5 仍未通过，M6/M7 保持锁定。
- DSH 交接包 v0.1.1 已生成并验证，SHA-256 为 `6399fd021dd48c0595d2da7b4d5b9e9e2995958f13bdcf359fadfaa2e1828f3c`；v0.1.0 和旧“主Anima”备份均保留。

## 2026-10-25（DSH 接手）

- 核验基线：HEAD `4c30eb8`，工作树干净；未重跑 Codex 已完成的 6 个任务。
- 预设 v0.1.1 SHA-256 与预期一致，`comfy-demo dsh verify` 通过（5 条）；经插件导入接口新增 5 条库记录，旧“主Anima”保留，库内共 6 条。
- 时崎狂三按 `benchmarks/characters.json` 以 `anima.standard.v1` 运行成功（seed 240201、832×1216、28 步、CFG 4.5，26.3 秒），输出 `E:\Comfy-Desktop\ComfyUI-Shared\output\anima_00003_.png`，补录 `client=dsh` manifest 并完成人工评分。
- 环境漂移：重启后 ComfyUI 为 **0.42.5**（交接时为 0.42.3）；`comfy/ldm/modules/attention.py` 在 v0.42.3 与当前字节一致，排除升级导致本次失败。
- `comfy-demo doctor` 通过（依赖 9/9、自定义节点 3/3、队列空、E 盘 175.49 GB）；`workflow validate --all --remote` 静态 5/5 无错误，但输出中没有逐工作流远程预检结论。
- 应用 `comfyui-anima-incontext-comfyui-0.42.3.diff`（用户关闭 Desktop 后备份并应用，`git apply --check` 与应用均 clean，`py_compile` 通过，节点目录无自带测试）。
- DSH 额外 in-context 测试在 KSampler 失败：`'AttentionTensorContainer' object has no attribute 'shape'`，prompt `3c705098…`，manifest 已保存为失败记录（`benchmark_task_id=null`，不计入正式任务）。
- 判定补丁只解决第一层（`preferred_attention`），第二层需要容器解包；按用户选择“B 保持现状、交回 Codex”，已写 `docs/M5_CODEX_HANDOFF_FROM_DSH.md`。M5 仍未通过，M6/M7 门禁保持锁定。
# 2026-10-26 公开准备开始

- 用户授权逐项实施公开准备，保持仓库私有；仅处理工程目录，网站由另一聊天维护。
- 已读取现有计划/发现/进度，开始 P1 隐私与来源核验。不会重跑生图或修改安装中的 ComfyUI。
- 通用配置、本机配置保全、离线测试隔离、legacy 入口保护和提交恢复修复完成。
- 当前完整测试 43 passed、无警告；Ruff、离线示例、5 条工作流静态检查、12 画布和 2 参考绑定哈希检查通过。
- 新建隔离环境 clean-d9b974bc46 安装与离线检查通过；同环境刷新最终源码后再次通过 43 项测试。证据保存在忽略目录 runs/public-readiness。
- 自有代码采用 MIT；来源依据用户明确声明；全历史规则扫描未命中常见凭据或大文件。下一步准备独立清理镜像与可恢复 bundle，推送前展示结果。
