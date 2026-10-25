# M5 交接给 DSH

## 交接边界

Codex 已完成 M0–M4、在线 doctor、5 条工作流远程预检、CLI 可承担的 6 个正式任务和官方 comfy-mcp 烟雾测试。M6 网页和 M7 个人网站均未开始。

DSH 不要重做已通过任务，不要修改历史图片、12 个画布工作流、`node_modules` 或私有 `workflows.json`。先读取 `DSH_IMPLEMENTATION_PLAN.md`、`docs/M5_LIVE_ACCEPTANCE_RUNBOOK.md`、`task_plan.md`、`findings.md` 和 `progress.md`。

## 已完成的正式任务

| 任务 | job_id | 工作流 | 结果 |
|---|---|---|---|
| 拉琪 img2img | `67abc395-1dc9-4687-8757-253f82420c96` | `larkie.img2img.v1` | 完成并评分 |
| 芙莉莲纠正性复测 | `f8234a7f-45c9-4194-bfe4-ae39f9c11534` | `animagine.standard.v1` | 完成并评分 |
| 喜多川海梦 | `e4265b17-a226-4680-90ca-cab1f792137a` | `anima.hq-2x.v1` | 完成并评分 |
| 蒸汽朋克工匠 | `b4ee7f3e-0b09-4313-9fbd-8c4d05f54572` | `anima.standard.v1` | 完成并评分 |
| 赛博夜行剑士 | `f4f95362-658d-45cb-9584-9869a0aba99c` | `animagine.standard.v1` | 完成并评分 |
| 海洋星象祭司 | `8e70b402-8ac3-4dd5-8825-4c1cd7fdbb4c` | `anima.hq-2x.v1` | 完成并评分 |

首次芙莉莲任务 `446ecc3a-8d95-4f1c-9a8b-47e83fc40bcb` 是保留的视觉失败样例，不能删除或覆盖。Codex comfy-mcp 烟雾测试 `63ea9097-f1f9-4a53-b684-6babdb9e1fbe` 已完成，输出为 `E:\Comfy-Desktop\ComfyUI-Shared\output\anima_00002_.png`。

## 唯一已知代码阻塞

拉琪 in-context 的 Codex 正式尝试 `68bf718b-2f19-4505-8b27-997a3fb1e2ec` 已通过 MCP 上传、预检和提交，但在 KSampler 失败：

```text
TypeError: ref_attn_op() got an unexpected keyword argument 'preferred_attention'
```

根因是 ComfyUI 0.42.3 的 `Attention.attn_op` 新增 `preferred_attention`，而本机自定义节点的包装函数仍使用旧签名。项目补丁只做兼容透传，不改工作流或模型：

```text
integrations/dsh/patches/comfyui-anima-incontext-comfyui-0.42.3.diff
```

目标文件：

```text
E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\custom_nodes\comfyui-anima-incontext\incontext.py
```

处理纪律：

1. 先只读核对目标函数仍与补丁前内容一致。
2. 要求用户手动关闭 ComfyUI Desktop，并确认 8188 已释放；DSH 不结束进程。
3. 复制一份带时间戳的源文件备份，再应用补丁；不要更新全部节点。
4. 运行 Python 语法检查和目标包自带测试（若测试存在）。
5. 由用户手动重开 Desktop；运行 `comfy-demo doctor` 和远程工作流校验。
6. 用 DSH 导入的 in-context 预设做一次额外测试。成功后仍需明确告诉用户：正式 `client=codex` 任务要回到 Codex 通过官方 comfy-mcp 重跑，不能把 DSH 结果伪装成 Codex 结果。

回滚：用户关闭 Desktop 后，用备份恢复 `incontext.py`，再由用户手动重开。

## DSH 仍需完成

1. 验证并通过 UI 导入 `integrations/dsh/releases/comfyui-demo-dsh-presets-v0.1.1.zip`；保留旧“主Anima”和 v0.1.0。
2. 用 DSH 官方插件按 `benchmarks/characters.json` 运行时崎狂三，固定 seed `240201`，将结果补录为 `client=dsh` manifest 并人工评分。
3. 按上节处理 in-context 兼容补丁并完成 DSH 额外测试。
4. 让用户回到 Codex 重跑正式拉琪 in-context；该任务成功并评分前，M5 仍是 `in_progress`。
5. M5 未通过前不得开始 M6；M6 未通过前不得修改个人网站。

每一步都报告修改文件、命令、真实结果、产物绝对路径、风险和回滚。相同错误连续三次必须停止；本问题已有一次失败，因此不得无改动重复提交。
