# M0–M4 离线实施报告

日期：2026-10-25

## M0：文档、基线与回滚

状态：通过。

- 保存工程总方案、DSH 执行方案和三份实施日志。
- E 盘当前检查值：总容量约 931.5 GB，可用约 175.52 GB；低于 50 GB 时 doctor 警告。
- 5 条 API 工作流复制后 SHA-256 与源文件一致。
- 12 条画布工作流已登记文件名、用途、节点数和 SHA-256；源文件未修改。
- DSH 旧“主Anima”已只读导出为 preset v1 备份。
- 旧项目脚本复制到 `legacy/`；历史图片仍在原目录。

回滚：使用 `legacy/` 恢复旧入口；DSH 可重新导入旧备份 ZIP。任何回滚都不得删除图片。

## M1：统一核心与生命周期

状态：通过。2026-10-25 在线 doctor 已确认服务、GPU、模型和节点。

- 建立 E 盘 `.venv`，实现配置、HTTP 客户端、doctor、错误分类和更新 runbook。
- HTTPX 对本地连接禁用环境代理，8188 未监听时 doctor 约 1.4 秒结构化失败。
- 活动代码无 subprocess、Popen、taskkill、ensure_server 或自动更新逻辑。
- `doctor --no-remote` 已验证工作区、输出目录、磁盘和静态工作流。

在线结果：ComfyUI 0.42.3、RTX 5070 Ti Laptop 约 12 GB，9 个模型依赖与 3 个关键节点全部可用；Desktop 使用 E 盘 Shared 输入/输出目录。

## M2：工作流注册与运行记录

状态：离线合约通过；真实提交待 M5。

- 5 条工作流进入 `workflows/registry.json`，节点 ID 不再散落在运行代码中。
- `seed=0`、边界、未知参数、参考图要求、镜像节点和唯一输出前缀均有测试。
- manifest 使用临时文件加 `os.replace` 原子写入。
- 输出解析只返回 ComfyUI 权威绝对路径，不下载副本。

## M3：CLI、热文件夹与兼容层

状态：离线通过。

- CLI 命令组已建立；`studio` 与公开导出按阶段门禁锁定。
- 热文件夹统一校验 JSON；失败请求进入 failed 并生成 `.error.json`。
- 四个旧 Python 入口和两个 bat 已转调新核心；旧源码保存在 `legacy/`。
- 兼容入口不再读取 DSH 私有库，也不再向项目下载图片。

## M4：DSH 与 Codex

状态：离线包与文档通过；DSH UI 导入和双端真实运行待用户操作/M5。

- 生成 5 工作流 preset v1 包及技能文件，3 条高风险流程为运行前必读。
- preset 内容与注册表工作流对象一致，包内声明注册表 SHA-256。
- Codex runbook 固定 server info、system stats、validate、async run、job、outputs 流程。
- DSH 私有 `workflows.json` 只读，未修改。

## 自动验证

```text
pytest: 17 passed
ruff: All checks passed
workflow validate --all: 5/5 passed
doctor (Desktop stopped): structured offline result, no process started
DSH bundle verify: preset v1, 5/5 workflows, skills present
```

## 当前阶段门禁

M5 尚未执行。必须由用户手动打开 ComfyUI Desktop 后，先完成在线 doctor 和 5 条工作流真实运行，再执行 8 个角色任务。M5 通过前不开发 M6 网页；M6 通过前不修改个人网站。
