# v0.1 公开准备与维护验收

更新：2026-10-26。目标是可安装、可离线验证的本地单用户工具；不是公网生成服务。
本文件记录工程准备，不授权把仓库改为公开，也不授权强推。网站由另一个聊天负责。

## 2026-10-26 历史替换与 CI 后续

- 用户审阅后明确同意替换私有 main 并运行 CI。远端旧提交核对为 d2cb5d9 后，以精确 force-with-lease 更新为清理后的 f2c2e7f；本地 main 同步，内容树不变，仓库保持私有。
- main 可达作者/提交者邮箱仅 noreply。私有 bundle 和本机 reflog 保留用于恢复，不随 Git 推送或公开分发；其他已有克隆须重新同步，避免把旧历史推回。
- 首轮 Actions 40291462472：Linux 3.11/3.13 通过，Windows 因 checkout 自动换行造成 API JSON 字节 SHA-256 变化而失败。维护者用 core.autocrlf=true 的独立克隆复现五条全部哈希不匹配。
- 新增 `.gitattributes` 固定正式 API 图为 LF。没有改动 JSON 图、注册哈希或取消校验。修复后的远端完整矩阵结果另行记录，不能用此前本机通过代替。
- 修复后本机 43 passed，Ruff 通过；core.autocrlf=true 的全新克隆中五条哈希全部匹配。修复提交 cc08c28，复验 Actions 40291884948。
- 隐私限制：GitHub 仅剩 main 分支引用，但认证 API 仍能按原 d2cb5d9 提交号查询旧对象。这证明 main 可达历史清理不等于服务端旧对象彻底移除；目前仓库仍私有。若公开前要求旧邮箱不可被旧 SHA 查询，还需另行处理托管端旧对象/缓存，或审阅新建的干净仓库方案；不得直接声称旧邮箱已从 GitHub 全部消失。
- 最终远端验收：[Actions 40291884948](https://github.com/znzky04/comfyui-agent-studio/actions/runs/40291884948)，代码提交 cc08c28，Windows/Linux × Python 3.11/3.13 四项全部 success。每项执行离线 pytest、Ruff、离线示例与 5 条工作流静态检查，不包含 GPU/浏览器新验收。后续只有文档结果更新，标记 skip ci，不重复消耗相同代码的矩阵。

## 已落实

- [x] 自有代码采用 MIT。作者明确声明工作流与参考节点为自己编写/搭建；记录在 `THIRD_PARTY_NOTICES.md`，没有据此重授权模型、第三方节点或角色图片。
- [x] 当前源码与可达历史进行常见凭据规则扫描；未命中所设规则，未发现已提交的图像、模型权重或 ZIP。报告仅在忽略的 `runs/public-readiness`，不自动公开。
- [x] 人工检查了 API 图中的默认提示词/参考图名与当前审批清单；无参考图二进制或运行 manifest 入库。历史文档保留部分环境路径与任务 ID，它们不是访问凭据。只展示批准的海梦单图，不扩大授权。
- [x] 通用模板不再依赖作者 E 盘。现有实际路径保全在忽略的 `config.local.toml`，配置中所有相对路径按仓库根目录解析。
- [x] 默认 pytest 不读取作者的 12 个外部画布和私人参考图。元数据契约仍校验；实际文件哈希由独立只读脚本显式检查。
- [x] 4 个 legacy Python 入口与 2 个历史 bat 禁用，防止误运行旧自动启动、私有库读取或下载副本路径。根目录兼容入口继续使用统一核心。
- [x] 接受每个远端任务后立即保存 ID、实际参数；中途失败继续观察已接受部分，批次最终标记失败，保留输出且不补交。
- [x] 提交中进程退出的记录保持可查询：观察已接受部分，超时标明 IncompleteSubmission。不能把未提交完的批次当成功。网络响应前的未知接受状态仍不能保证恰好一次。
- [x] TestClient 改用独立开发依赖 httpx2，保留运行时 HTTPX。没有降级或改动 ComfyUI 环境来消除警告。
- [x] CI 配置 Windows/Linux × Python 3.11/3.13 离线检查；不需要 GPU、模型、私人图片或外部节点。
- [x] README 明确源码 editable 安装、配置优先级、安全边界、未实现出口和实验工作流；补充 SECURITY / CONTRIBUTING / 上游归属。
- [x] 后续本机 Git 提交邮箱设为通过 GitHub 账号 ID 核对的 noreply，仅修改本仓库配置。

## 验证命令与证据

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts examples
.\.venv\Scripts\python.exe examples/offline_review.py
.\.venv\Scripts\comfy-demo.exe workflow validate --all
.\.venv\Scripts\python.exe scripts/check_clean_install.py
.\.venv\Scripts\python.exe scripts/audit_repository.py --report runs/public-readiness/privacy-audit.json
```

干净安装脚本仅复制 Git 管理/未忽略的源码，创建独立虚拟环境，不带 `.venv`、`config.local.toml`、画布原件、图库和参考图。通过 PyPI 安装依赖，需要网络；测试与示例本身离线。构建依赖显式安装后使用 `--no-build-isolation`，避免维护者环境的隔离构建下载长时间无输出。首次失败记录保留，不能计为通过。

本机原件另行检查，路径由操作者显式指定：

```powershell
.\.venv\Scripts\python.exe scripts/check_local_baselines.py --source-root <原始画布目录> --reference-root <参考图目录>
```

维护者 12 条画布和 2 处参考绑定已只读核验，哈希保持不变。该检查不放入公共 CI，也不删除/改动原件。

完整本轮结果、干净环境路径与历史清理审阅结果由下方最终记录追加。历史 33 项是此前验收，不能作为新源码的测试数量；历史 GPU/浏览器结果仍保留原日期，本轮没有新的 GPU 验收。

### 2026-10-26 实际结果

- 当前源码：43 passed，无警告；Ruff 通过，离线示例通过，5 条 API 静态校验零错误。
- 独立 Windows / Python 3.13 环境：`runs/public-readiness/clean-d9b974bc46`；从空环境安装，未复制本机配置和参考图。安装的 Pydantic 2.14.1 与原环境 2.13.4 不同，实际测试仍通过。
- 独立环境刷新最终源码后再次 43 passed；Ruff、离线示例、5 条 API 静态校验与 `pip check` 均通过。`final-*.log` 及源码哈希清单保留于该目录。
- 仓库目录以外的 CLI 工作流列表查询通过。首个隔离构建失败目录保留为证据，不计入通过。
- 未运行 Linux / Python 3.11 / 浏览器 / GPU 新验收；CI 矩阵等更新私有远端后执行。
- 本轮临时环境与报告约 111 MiB；E 盘余量仍充足，图片未增删。
- 已用 git-filter-repo 在独立镜像完成作者/提交者邮箱清理，仅保留经 GitHub 账号 ID 核对的 noreply。提交数量和 main 内容树一致，原私有历史 bundle 通过 Git 校验；源工作区和远端引用尚未替换。
- 历史审阅报告与可恢复备份位于忽略目录 `runs/public-readiness/history-*/`；`review.json` 含清理前后提交 ID。不要提交 bundle、mailmap 或清理镜像。最终镜像需要纳入本说明的最后一次文档提交，推送前以最新 review.json 为准。
- 在最终镜像获批并更新远端之前，不应直接公开当前远端或从原历史分支推送，否则旧邮箱仍会可见。网站聊天也应避免推送工程仓库的旧历史。

## 公开前的最后步骤

1. 审阅邮箱清理后的历史：作者/提交者仅为 noreply，主分支内容树、提交数量与原来一致；私有 bundle 已验证可恢复。
2. 用户审阅后再明确授权远端历史替换。推送前重新核对远端 main 未被其他聊天更新，不无条件覆盖他人提交。
3. 已完成私有远端 CI 四环境矩阵（Actions 40291884948）；代码变更后需重新验证。公开前另处理上方已证实的旧 SHA 对象访问问题。
4. 维护者在 GitHub 检查并按可用能力开启 private vulnerability reporting / push protection。此轮不修改托管安全设置。
5. 另行确认仓库公开。未经授权不改可见性、不部署网站、不发布模型/图片或安装包。

## 可带限制公开的功能

- DSH v0.1.2 UI 重导入尚未执行，标为待验收；生成 ZIP/官方参数函数验证不等于 UI 验收。没有启动 DSH 或擅自重跑生图。
- 拉琪 in-context 技术通过、视觉不合格，保留为实验能力。完整参考节点未分发，第三方克隆者需要自行准备兼容依赖。
- `showcase export` 是明确返回错误的未实现占位，已从可用功能承诺中排除；不要求为了公开而新增一套导出系统。
- 不承诺跨设备像素级复现、跨机器事务、多人协作或自动内容审核。

## 回滚

源码按 Git 提交审阅和 revert；不要 hard reset 或清理工作区。忽略的本机配置恢复原路径即可。历史清理先在独立镜像进行，用户批准后才替换源引用及私有远端；`before.bundle` 是私有备份，包含原邮箱，绝不能作为公开发行资产。恢复旧历史也需明确授权与远端比较，避免撤销新邮箱清理或覆盖后续提交。临时安装、日志和镜像保留在 runs/public-readiness，手动审阅后可只清理自己创建的验收目录，不能清理图片/参考图/画布。
