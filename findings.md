# Findings

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

## 外部集成

- Codex 已配置官方 `comfy-mcp` 精简工具白名单，目标为 `127.0.0.1:8188`。
- DSH 安装 `dsh-comfyui 0.5.5`，支持预设 ZIP v1、参数和技能包。
- DSH 预设导入永远创建新记录，不覆盖旧工作流。
- ComfyUI 当前环境曾记录为 0.42.3、Python 3.13.12、RTX 5070 Ti Laptop 12GB。
- 当前 8188 未监听；doctor 能在约 1.4 秒内返回“请手动打开 Desktop”，且未启动任何进程。

## 网站

- 目标个人网站位于 `D:\VibeCoding\Personal web\v2`。
- 技术栈为 React 19、Vite、React Router、Tailwind、GSAP/Motion。
- 当前分支为 `codex/larkie-web-pet`，存在未跟踪 `scripts/`，M7 不得覆盖。
- 项目内容由 `src/content/projects.ts` 统一提供，现有四个项目的内容契约必须保留。
