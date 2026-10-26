# 后续工程审查与修复

2026-10-26，起点 main e2100d2。范围是统一核心、HTTP 客户端、任务文件、热文件夹和参考图参数；没有修改网站、ComfyUI 安装、模型、正式 API JSON、原始画布、图库或公开图片审批。

## 修复内容

| 问题与触发 | 原行为 | 修复 |
| --- | --- | --- |
| 远端清理历史后刷新任务 | 用远端现有结果覆盖本地已知输出，可能清空图片路径 | 合并并去重，保留以前记录过的路径 |
| 取消含已完成图的批次 | 未收集已完成图；已全部完成也会被标成 cancelled | 先收集历史，只取消未结束项；全完成保留 completed，已有失败按失败记录 |
| 取消后紧接着失去连接 | 后续观察失败可能影响取消记录 | 已接受的取消仍记录 cancelled，保留此前收集的输出 |
| 同步等待遇到错误历史 | 错误历史可能已有成功保存的图片，但 wait 抛错后漏记 | 失败时尽力补录历史中的输出；网络错误不覆盖原始错误、不丢旧路径 |
| wait 读到 completed=false | 将尚未完成直接视为失败 | 显式 error 才失败；等待 completed=true |
| 客户端取消恰逢任务切换 | 全局 interrupt 可能作用于别的任务；仅删队列也可能漏掉刚开始的目标 | 先删除该 prompt_id 排队项，再以 prompt_id 定向中断，无全局回退 |
| 服务端返回异常文件路径/存储类型 | CLI 可能接收越出对应根目录的路径 | 只接受 output/input/temp，并验证解析后的路径仍在对应根目录 |
| 同一记录同时保存 | 固定 .json.tmp 互相覆盖，可能 FileNotFoundError 或混用中间内容 | 每次创建同目录唯一临时文件，再原子替换，只清理自己的临时文件 |
| 请求同名、旧 processing 或孤立 error.json | 热文件夹归档可能覆盖旧请求或错误证据 | 独占预留目标；冲突生成唯一名称；已被接管的请求跳过 |
| 单参考节点收到两张图 | 接受请求但只使用第一张 | 明确拒绝，避免用户误以为两张都已参与生成 |
| 任务 ID 含路径/通配符 | 存储层直接参与 glob/路径拼接 | 存储层限制为 1–128 个 ASCII 字母、数字、下划线和短横线 |

定向中断的依据是对现有 ComfyUI 0.42.x `server.py` 的只读核查：`/interrupt` 接受并检查 prompt_id。本轮只验证客户端请求契约，没有实际中断 GPU 任务。运行时要求后端支持该参数；旧版或自定义后端若忽略它，不能沿用此取消保证。

## 验证

- 首批保留逻辑回归在修复前复现 8 个失败；固定临时文件的并发冲突另行确定性复现；客户端定向中断/路径边界另外复现 3 个失败。
- 最初测试目录父目录未创建导致 fixture 错误，建目录后重新复现；fixture 错误不计为产品缺陷。Ruff 的 ClassVar 提示已修复。
- 完整离线 pytest：**65 passed，无警告**。Ruff、离线示例与 5 条 API 工作流静态校验通过。
- 12 个原始画布与两处参考图绑定的本机哈希检查通过；5 条注册 API JSON、原始哈希清单与公开选图审批没有修改。
- 新增/扩展测试：`test_retention_regressions.py`、`test_client_boundaries.py`、`test_inbox.py`、`test_manifests.py`。使用替身后端和测试临时文件，未生成新图。
- 本机证据在忽略的 `runs/engineering-review`。远端 CI 结果单独追加，不能将此前 43 项的 CI 当成本轮代码验收。

最终远端结果：修复提交 `fcc6b2e` 的 [Actions 40295864777](https://github.com/znzky04/comfyui-agent-studio/actions/runs/40295864777) 四环境全部通过（Windows/Linux × Python 3.11/3.13）；每个环境 65 项测试、Ruff、离线示例及工作流静态校验通过。日志核对保存在忽略的 runs/engineering-review/ci-40295864777。后续仅文档结果更新，不修改已验证代码。

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts examples
.\.venv\Scripts\python.exe examples/offline_review.py
.\.venv\Scripts\comfy-demo.exe workflow validate --all
```

## 当前限制与来源更正

- 唯一临时文件与原子替换不是跨进程事务。多个独立进程同时修改同一任务，仍可能出现逻辑上的最后写入覆盖。Web 内已有 refresh/cancel 序列化；本轮没有将存储重构为数据库或承诺多进程协调。
- 文件仍保留不代表旧的漏记 manifest 会被自动补全。本轮没有扫描或重写用户历史记录；新逻辑保护后续观察/取消/等待。
- DSH 新预设 UI 导入与拉琪 in-context 视觉不足仍保持既有状态，未以离线测试冒充新的实际生图验收。
- 用户接受旧 SHA/邮箱残留，明确不再隔离；不继续为此重写历史。
- 用户更正部分工作流来自网上下载且作者不明。撤回“全部工作流自有/MIT”，图 JSON 暂排除在 MIT 授权外。仅加声明不能补足分发许可，完整仓库继续私有，公开前核实来源或改变发布范围。节点原有独立声明不扩大解释为所有下载图的授权。
- 若工作台已在运行，需要下次启动工作台加载新代码；不要因此重启或更新用户的 ComfyUI Desktop。

源码可按本轮 Git 提交审阅并 revert。不要恢复旧 Git 历史，不删除 runs、图片、原始画布或本机配置。
