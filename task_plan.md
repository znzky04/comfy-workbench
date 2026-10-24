# ComfyUI Agent Studio v2 实施计划

## 目标

把现有 `comfyui-demo` 升级为由项目版本库统一管理、同时服务 Codex、DSH、CLI、热文件夹和本地网页的作品集级 ComfyUI 工程；图片只保存在 ComfyUI 的 E 盘权威图库，既有图片和原始工作流永不自动删除。

## 固定决策

- ComfyUI Desktop 由用户手动启动、停止和更新。
- 项目版本库是工作流、参数和技能包的唯一权威来源。
- 5 条 API 工作流进入首轮正式支持，12 条画布工作流只读登记。
- DSH 使用官方 `dsh-comfyui` 预设包导入，不改插件源码或私有数据库。
- 顺序为：核心 → CLI/热文件夹 → DSH/Codex → 真实生图 → 本地网页 → 个人网站。
- 真实生图评测集为 2 拉琪、3 热门动漫角色、3 其他原创角色。

## 阶段

| 阶段 | 状态 | 完成条件 |
|---|---|---|
| M0 文档、基线、回滚 | in_progress | 方案文档、哈希、DSH 备份、Git、磁盘记录完成 |
| M1 统一核心与生命周期 | offline_passed | 核心、doctor 和无自动启停已验；在线环境检查待 Desktop |
| M2 工作流注册与运行记录 | offline_passed | 5 条注册、12 条登记、schema 和 manifest 已验 |
| M3 CLI、热文件夹、兼容包装 | offline_passed | 新 CLI、热文件失败留证和兼容包装已验 |
| M4 DSH/Codex 集成 | offline_passed | DSH ZIP/技能包/runbook 已验；UI 导入待 M5 |
| M5 真实生图验收 | pending | 8 个角色任务及 DSH/Codex 各一次真实提交 |
| M6 本地网页 | pending | FastAPI 工作台、SSE、上传、历史、视觉和浏览器测试 |
| M7 个人网站项目页 | pending | 精选导出、项目页、网站构建与回归测试 |

## 当前约束

- 不删除、覆盖或移动现有生成图片。
- 不修改 12 个原始画布工作流。
- 不修改 `dsh-comfyui` 的 `node_modules` 或直接写 `workflows.json`。
- 不在用户未确认时发布网站或调用付费 API。
- 个人网站存在未提交文件，M7 开始时必须重新检查并避让。

## 错误记录

| 错误 | 次数 | 处理 |
|---|---:|---|
| 初次 E 盘余量检查未产生输出 | 1 | M0 改用 CIM/文件系统查询重新检查 |
| pip 默认构建隔离无输出等待 | 1 | 停止等待，改用 isolated/no-cache/no-input 显式安装 |
| pip 直接依赖安装无输出等待 | 1 | 停止等待，使用显式 PyPI 和关闭缓存后成功 |
| editable 构建缺少 `editables` | 1 | 补装 `editables`，随后 editable 安装成功 |
| doctor 在系统代理下访问本机 8188 返回 502 | 1 | HTTPX 设置 `trust_env=False`，端口关闭时直接结构化返回 |
| 清理自建 pip 临时目录被安全策略拒绝 | 2 | 已加入 `.gitignore`，不再尝试删除，不影响工程或 Git |

