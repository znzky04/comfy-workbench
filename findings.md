# Findings

## Codex 再接手（2026-10-25）

- 已只读解压并核对 DSH 会话 `session-c184de8b-6602-4d29-a8c7-e685336db7a1`；末轮确认为用户选择保持第一层补丁、交回 Codex，提交为 `b3daf0b`。
- 接手时 Desktop 已关闭：8188 未监听，也无 ComfyUI main.py 进程。节点文件 SHA-256 与 DSH 交接完全一致，E 盘余量约 173.59 GiB。
- 先用本机 ComfyUI 的真实 `AttentionTensorContainer` 和 `wrap_attn` 定义重现容器失败，再修复节点：形状检查只 peek，回退保留原容器和参数，仅自定义 SDPA 分支 take。参考偏置计算保持不变。
- 第一版容器解包发现 PyTorch Tensor 也有带索引的 take 方法；改为先识别原始 Tensor，避免旧接口回归。6 项 CPU 针对性测试通过，包含真实容器、普通 Tensor、禁用/中性/序列不匹配回退和核心 container_function override。
- 运行中的服务没有被自动管理；已请求用户手动打开 Desktop，真实采样仍待启动后执行。
- 后续真实 GPU 验证成功：用户打开 Desktop 后，原参数正式 in-context 任务完整执行 88.02 秒，两个接口故障均未复现。输出保留于 Shared/output/comfyui-demo/2026-10-25/larkie-incontext-v1。
- 兼容修复解决了执行问题，没有解决模型的身份保持质量：这张图只保住月白发和蓝翼，服装、面部及金色环偏离参考和 brief。不得将技术成功写成视觉通过。

## 当前工程

- 项目根目录不是 Git 仓库。
- E 盘总容量约 931.5 GB，2026-10-25 当前可用约 175.52 GB；代码与文档预计低于 20 MB，项目虚拟环境预计 100–300 MB，图片会持续增长且不自动清理。
- 存在 5 个 API 工作流：Anima 标准、Anima 2×、Animagine、拉琪图生图、拉琪 in-context。
- ComfyUI 用户目录存在 12 个原始画布工作流。
- 当前 Python 入口重复实现提交、轮询和下载；网页和热文件夹会自动启动 ComfyUI。
- `gen_from_their_workflow.py` 读取 DSH 私有 `workflows.json`。
- 当前 `output/` 与 `kurumi/` 包含需要永久保留的历史图片。
- `output/` 约 27.04 MB，`kurumi/` 约 36.27 MB，均只做原地保留。

## 工作流基线

- 5 个 API 工作流已计算 SHA-256，后续复制到 `workflows/api/` 时必须保持字节一致。
- 12 个画布工作流已计算 SHA-256；它们位于 ComfyUI 用户目录，只登记、不修改。
- API 节点映射已定位：Anima 使用提示词 20/21、尺寸 30、采样器 40；Animagine 使用 2/3/4/5；拉琪图生图额外使用 30/31；拉琪 in-context 使用 10/12/15/20/21/22/23。
- 首次真实运行 `animagine.standard.v1` 虽然任务完成，但输出为金色对称抽象图形、完全没有人物；原图和失败评分均已保留。
- Animagine 深入诊断确认：PNG 内嵌 API 请求参数正确，ComfyUI 日志把模型识别为 `SDXL`/`EPS` 并正常加载自带 `AutoencoderKL`，28 步无运行错误；模型元数据声明为 Animagine XL 4.0 Opt，文件 SHA-256 为 `6327eca98bfb6538dd7a4edce22484a1bbc57a8cff6b11d075d40da1afb847ac`。结构链路和模型类型没有发现错误。
- 官方模型卡明确要求标签式提示词、以质量增强标签收尾，并推荐 Euler a、28 步、CFG 5、832×1216。采样参数原本已符合，首次提示词却以质量词开头、缺少 `1girl` 且夹有自然语言式评测短语；因此改用严格标签顺序和新 seed 做一次有依据的纠正性复测，不进行同参盲重试。
- Animagine 纠正性复测成功，说明模型和 API 链路正常；芙莉莲首次视觉失败图仍原样保留。
- `larkie.incontext.v1` 经官方 comfy-mcp 上传、预检和提交后，在 KSampler 暴露 `preferred_attention` 签名不兼容。ComfyUI 0.42.3 会把该关键字传给 `attn_op`，本机 `comfyui-anima-incontext/incontext.py` 的旧包装函数未接收额外关键字。项目已保存最小兼容补丁，但运行中的 Desktop 未被修改或重启。
- 同一 MCP 随后成功运行不依赖该节点的 `anima.standard.v1`，证明 Codex MCP 的连接、提交、轮询和输出链路本身正常；阻塞范围仅限 in-context 自定义节点。

## 外部集成

- Codex 已配置官方 `comfy-mcp` 精简工具白名单，目标为 `127.0.0.1:8188`。
- 2026-10-25 复核发现 comfy-cli 默认工作区曾漂移到 C 盘默认目录；已通过官方 `set-default` 纠正为 `E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI`，`server_info` 已确认新路径。
- DSH 安装 `dsh-comfyui 0.5.5`，支持预设 ZIP v1、参数和技能包。
- 2026-10-25 DSH 实测：v0.1.1 预设经插件导入接口新增 5 条运行工作流（新 id），旧「主Anima」保留，库内共 6 条；导入不覆盖既有记录。
- DSH 用时崎狂三任务实际提交成功（`client=dsh`，seed 240201），说明插件参数覆盖与提交链路可用；其输出沿用工作流内置 `SaveImage` 前缀 `anima`，未走项目唯一前缀约定。
- 2026-10-25 重启后环境为 ComfyUI **0.42.5**；`comfy/ldm/modules/attention.py` 的 blob 在 v0.42.3 与当前完全一致（`abed292b…`），因此后续 in-context 失败不是升级引入。
- in-context 兼容是**两层**问题：第一层 `preferred_attention` 关键字（已由 0.42.3 补丁解决），第二层 `Attention.forward` 把 q/k/v 包成 `AttentionTensorContainer` 后仍调用 `self.attn_op`，节点内函数按 Tensor 取 `.shape` 失败。补丁只解决第一层，第二层未动，交回 Codex 处理。
- DSH 预设导入永远创建新记录，不覆盖旧工作流。
- ComfyUI 当前环境曾记录为 0.42.3、Python 3.13.12、RTX 5070 Ti Laptop 12GB。
- 当前 8188 未监听；doctor 能在约 1.4 秒内返回“请手动打开 Desktop”，且未启动任何进程。
- comfy-mcp 的 freshness 检查曾在 15 秒超时，但不影响工作区识别；待 Desktop 启动后重新验证服务、版本和依赖。
- 2026-10-25 在线复核：Comfy Desktop 窗口已启动；最初看到的两个 PID 实为 Desktop 启动器及其 `standalone-env` 子 Python，不是两个独立实例。日志随后显示服务器开始监听 `127.0.0.1:8188`。
- Desktop 启动参数把输入/输出目录重定向到 `E:\Comfy-Desktop\ComfyUI-Shared\input` 和 `E:\Comfy-Desktop\ComfyUI-Shared\output`；在线前必须据此纠正项目权威输出配置，不能继续假设工作区内的 `output/` 是实际图库。
- 官方 MCP 已在线确认 ComfyUI 0.42.3、Python 3.13.12、PyTorch 2.10.0+cu130；RTX 5070 Ti Laptop 总显存 12,820,480,000 bytes、空闲 11,561,598,976 bytes，HQ 任务应串行。
- Desktop Shared input 中暂时没有 `larkie_reference_key_art.webp`；统一核心会从旧 input 源文件经 HTTP 上传为内容哈希文件名，避免覆盖。

## 网站

- 目标个人网站位于 `D:\VibeCoding\Personal web\v2`。
- 技术栈为 React 19、Vite、React Router、Tailwind、GSAP/Motion。
- 当前分支为 `codex/larkie-web-pet`，存在未跟踪 `scripts/`，M7 不得覆盖。
- 项目内容由 `src/content/projects.ts` 统一提供，现有四个项目的内容契约必须保留。
