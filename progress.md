# Progress

## 2026-10-25（Codex 再接手）

- 阅读 DSH 原始压缩会话、提交 b3daf0b 和交回文档，确认狂三已完成，阻塞在 in-context 容器接口。
- Desktop 关闭期间备份节点为 `incontext.py.bak-codex-containers-20261025-184155`，完成第二层容器兼容修复。
- 新增 `scripts/check_anima_attention_compat.py`：修复前 2 项容器测试复现原故障；修复后 6 项全部通过。运行使用 ComfyUI 自带 torch，不新增依赖。
- 下一步：记录版本化补丁、复核项目测试，然后等待用户手动打开 Desktop，使用官方 comfy-mcp 运行正式拉琪 in-context。
- 版本化容器补丁已保存，反向适用性检查通过；节点最终 SHA-256 为 `ee9b7f3c4d275779ff4717c5bee3024f6e8b6a2deb8d48c4d1a1b8351375e4e3`。
- 最终离线验收：项目 pytest 19 passed，维护范围 Ruff 通过，5/5 注册工作流静态校验通过，注意力专项 6/6 通过。详细恢复/回滚记录见 `docs/ANIMA_ATTENTION_COMPATIBILITY.md`。

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
