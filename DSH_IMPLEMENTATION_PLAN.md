# DSH 执行方案：ComfyUI Agent Studio v2

## 执行总则

按 M0 → M7 顺序执行，一次只完成一个里程碑，每阶段独立提交。每个阶段结束必须报告修改文件、测试命令、实际结果、产物路径、剩余风险和回滚方法。

绝对禁止：

- [ ] 不启动、强杀或更新 ComfyUI Desktop。
- [ ] 不修改 `dsh-comfyui` 的 `node_modules`。
- [ ] 不直接读写 DSH 私有 `workflows.json` 作为运行依赖。
- [ ] 不删除、移动或覆盖任何生成图片。
- [ ] 不修改 12 个原始画布工作流。
- [ ] M5 未通过前不开发网页；M6 未通过前不修改个人网站。
- [ ] 热门角色只使用本地生成结果，不抓取官方图、Logo 或宣传资产。
- [ ] 同一错误连续三次后停止并报告，不继续盲试。

## M0：基线与回滚

- [ ] 阅读 `ENGINEERING_UPGRADE_PLAN.md` 和本文件。
- [ ] 检查 E 盘余量并记录。
- [ ] 为 5 个 API JSON 与 12 个画布 JSON 计算 SHA-256。
- [ ] 只读导出当前“主Anima”为 preset v1 备份 ZIP。
- [ ] 确认 `output/`、`kurumi/` 原地保留且未进入 Git。
- [ ] 初始化 Git，并确认本机配置、缓存、日志、运行记录、模型和图片均被忽略。
- [ ] 更新 `task_plan.md`、`findings.md`、`progress.md`。

验收命令：

```powershell
git status --short
git check-ignore output kurumi runs config.local.toml .venv
Get-FileHash .\workflows\api\*.json -Algorithm SHA256
```

回滚：删除仅由 M0 新建且尚未提交的文本骨架；不得触碰旧图片、旧工作流或 DSH 数据。

## M1：统一核心和生命周期

- [ ] 在项目根目录创建 `.venv`，所有依赖安装在 E 盘。
- [ ] 实现配置、请求 schema、`ComfyClient`、错误分类和 `doctor`。
- [ ] 客户端支持健康检查、系统状态、校验、上传、提交、状态、等待、取消和输出解析。
- [ ] 搜索并解除所有自动启动/结束 ComfyUI 的调用。
- [ ] 服务未运行时 5 秒内失败，并提示用户手动打开 Desktop。
- [ ] 增加 ComfyUI 安全更新 runbook。

验收：运行单元测试；在 8188 未监听时运行 `comfy-demo doctor`，确认只报诊断、不启动进程。

## M2：工作流注册与任务记录

- [ ] 迁入并锁定 5 条 API 工作流。
- [ ] 建立 `workflows/registry.json` 与 schema 校验。
- [ ] 建立 `workflows/source_manifest.json`，登记 12 条画布工作流，不修改源文件。
- [ ] 所有参数通过注册表映射，运行代码不得硬编码节点 ID。
- [ ] `seed=0` 保持为 0；仅缺省和 `-1` 随机化。
- [ ] 图生图/in-context 必须校验参考图。
- [ ] 每次任务原子写入 `runs/YYYY/MM/<job-id>.json`。
- [ ] 输出使用唯一前缀，返回 ComfyUI 权威绝对路径，不复制图片。

验收：5 条 JSON 可解析，所有映射的节点和 input key 存在，12 条原始哈希与基线相同。

## M3：CLI、热文件夹与兼容入口

- [ ] 实现 `doctor`、`workflow`、`run`、`job`、`watch`、`studio`、`dsh`、`showcase` 命令。
- [ ] 热文件按 pending → processing → done/failed 迁移。
- [ ] 失败时保留原请求并生成同名 `.error.json`。
- [ ] `run_comfy.py`、`gen_from_their_workflow.py`、`inbox_watch.py`、`anima_studio.py` 只做兼容转调。
- [ ] bat 文件显式使用项目 `.venv` 并显示迁移提示。

验收：旧命令仍能进入新实现；无代码读取 DSH 私有库或启动 ComfyUI。

## M4：DSH 与 Codex 闭环

- [ ] 生成 `comfyui-demo-dsh-presets-v<version>.zip`。
- [ ] ZIP manifest 格式为 `dsh-comfyui-workflow-preset` v1，包含 5 条正式工作流。
- [ ] 每条包含参数、标签；HQ、img2img、in-context 设为运行前必读。
- [ ] 技能包写明显存、参考图、参数、常见失败和权威输出路径。
- [ ] 写 `integrations/codex/RUNBOOK.md`，固定校验、异步提交、轮询和路径报告流程。
- [ ] 导入 DSH 新包前再次导出旧包；新旧并存测试，禁止覆盖。

验收：`comfy-demo dsh verify <zip>` 通过，ZIP 内工作流哈希与注册表一致，Codex runbook 与注册表 ID 一致。

## M5：8 个角色真实验收

最终名单：

- [ ] 拉琪 img2img
- [ ] 拉琪 in-context
- [ ] 时崎狂三
- [ ] 芙莉莲
- [ ] 喜多川海梦
- [ ] 赤铜短发机械义肢蒸汽朋克工匠
- [ ] 墨蓝长发赛博夜行剑士
- [ ] 青绿色波浪长发海洋星象祭司

要求：覆盖 5 条工作流；DSH 与 Codex 至少各提交一次；每次记录版本、哈希、prompt、negative、seed、尺寸、steps、CFG、参考图哈希、模型/LoRA、时间、绝对输出路径和人工评分。视觉未通过的图片也必须保留。

## M6：本地网页

前置条件：M5 全部通过。

- [ ] FastAPI 只调用统一核心并监听 `127.0.0.1:8199`。
- [ ] 实现 health、workflows、uploads、jobs、SSE、cancel、artifacts API。
- [ ] 实现历史、多图画廊、manifest 与评测筛选。
- [ ] 使用月白/幽蓝/金色星夜视觉，支持移动端与 reduced motion。
- [ ] 完成功能、错误、上传和浏览器回归测试。

## M7：个人网站

前置条件：M6 全部通过。

- [ ] 开始前检查 `D:\VibeCoding\Personal web\v2` 的 Git 状态并保护用户修改。
- [ ] 只增加第五个项目、详情路由、详情页与独立资产。
- [ ] 更新内容契约“四个项目”为“五个项目”。
- [ ] 原创角色作为主要作品；热门角色单独归入非商业同人技术评测。
- [ ] 清晰展示 AI 生成、权利归属和无官方隶属/背书声明。
- [ ] 运行 lint、build、桌面/移动 Playwright 与原功能回归。
- [ ] 不执行 Vercel 发布。

## 阶段报告模板

```text
里程碑：M?
状态：通过 / 未通过 / 阻塞
修改文件：
执行命令：
实际测试结果：
产物绝对路径：
剩余风险：
回滚方法：
下一阶段门禁：
```
