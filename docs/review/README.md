# Comfy Workbench — Core Source Review

A review snapshot of the Python engineering layer: request validation, workflow registry,
parameter mapping, persistent task records and backend reconciliation.

这是从实际工程提取的本地源码审阅包。它不是完整生图发行版：不包含生产工作流、模型、参考图、图库、运行记录、私人提示词或本机配置。2026-10-26 用户选择先使用私有 GitHub 仓库，因此此包仅留作本地审阅，不再通过网站提供下载。完整源码位于 https://github.com/znzky04/comfy-workbench ，需要仓库访问权限。

## Installation / 安装

Python 3.11 或以上。解压后在包根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe examples/offline_review.py
.\.venv\Scripts\python.exe -m pytest -q
```

macOS/Linux 对应使用 `.venv/bin/python`。无需启动 ComfyUI，也不下载模型。

离线示例在包内 `runs/offline-review` 下创建临时 JSON，退出时清理该临时目录。它演示参数绑定、seed 0、输出命名、记录重载和哈希漂移检测。示例图只是契约夹具，不能提交给 GPU 生图。

## What to read / 阅读顺序

| 文件 | 工程问题 |
| --- | --- |
| `src/comfyui_agent_studio/models.py` | 请求约束和任务数据结构 |
| `src/comfyui_agent_studio/registry.py` | 哈希校验、参数映射和工作流深拷贝 |
| `src/comfyui_agent_studio/manifests.py` | 临时文件替换写入和状态转换约束 |
| `src/comfyui_agent_studio/service.py` | 任务身份持久化、状态恢复和部分结果保留 |
| `docs/ENGINEERING_DECISIONS.md` | 两个决策案例、取舍与证据 |

`src` 内的 Python 源码来自实际工程。`config.example.toml` 是审阅包专用的相对路径示例，不包含作者机器的目录。完整工作台与生成 CLI 还需要生产工作流、上游模型与额外 Web 依赖，因此不作为此精简包的运行入口。

## Verification / 验证范围

包内可运行测试为请求模型与 manifest 存储测试节选。完整工程在 2026-10-26 的验收记录为 33 项通过；精简包测试不等同于完整工程或真实 GPU 验收。

`evidence/test_job_refresh.py.txt` 为实际工程中的恢复测试源码，便于审阅替身后端如何验证“不重复提交”。它依赖完整工程夹具，不列入本包可运行测试。当前文件存储没有跨文件事务或跨机器协调能力。

## Attribution / 归属

工程由作者借助 Codex / DSH 完成实现与验证。ComfyUI、生成模型和官方客户端属于上游组件；此包不分发模型权重、官方插件或图像资产。

此包供源码审阅，未附加新的开源许可授权。`SNAPSHOT.json` 列出快照来源与包含文件的 SHA-256；不包含 Git 历史。
