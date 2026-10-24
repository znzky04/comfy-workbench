# M5 真实生图验收 Runbook

## 门禁

1. 用户手动打开 ComfyUI Desktop。
2. 运行 `comfy-demo doctor`，要求连接、GPU/显存、模型和节点全部通过。
3. 运行 `comfy-demo workflow validate --all --remote`。
4. DSH 导入 `integrations/dsh/releases/comfyui-demo-dsh-presets-v0.1.0.zip`，保留旧“主Anima”。
5. 不安装缺失依赖、不修改工作流、不删除任何图片；若依赖缺失，先报告并由用户决定。

## 固定任务与客户端

权威请求位于 `benchmarks/characters.json`。

| 任务 | 工作流 | 客户端 |
|---|---|---|
| 拉琪 img2img | `larkie.img2img.v1` | CLI |
| 拉琪 in-context | `larkie.incontext.v1` | Codex comfy-mcp |
| 时崎狂三 | `anima.standard.v1` | DSH |
| 芙莉莲 | `animagine.standard.v1` | CLI |
| 喜多川海梦 | `anima.hq-2x.v1` | CLI |
| 蒸汽朋克工匠 | `anima.standard.v1` | CLI |
| 赛博夜行剑士 | `animagine.standard.v1` | CLI |
| 海洋星象祭司 | `anima.hq-2x.v1` | CLI |

拉琪参考图：

```text
E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\input\larkie_reference_key_art.webp
SHA-256: dd08bff4141b774db93c5ecac1d4d916660afbce496f13f9215e9e042cb1dac2
```

## 执行纪律

- 按清单逐项执行，一次只跑一个 HQ 任务。
- Codex 使用 `integrations/codex/RUNBOOK.md` 的固定调用顺序。
- DSH 运行“时崎狂三”时必须显式输入清单中的 seed 和参数，避免插件随机 seed。
- 每个任务完成后立即检查 `runs/YYYY/MM/<job-id>.json` 的工作流哈希、实际 seed、输出绝对路径和结束状态。
- MCP 或 DSH 直接提交的任务若未走 CLI，使用同一字段人工补录 manifest，不允许缺失来源。
- 图片不论视觉好坏都保留；只在评分中标记问题。

## 人工评分

每张图填写 1–5 分：角色身份/标志特征、构图、人体、材质与细节、总体质量，并记录问题。拉琪额外比较图生图和 in-context 的身份保持；热门角色只评价技术还原，不使用官方图作为页面素材。

## 通过条件

- 8 个任务都有终态 manifest 和至少一个权威输出路径。
- 5 条工作流均至少成功一次；HQ 至少覆盖一个热门角色和一个原创角色。
- Codex 与 DSH 各有至少一次成功提交，并与注册表 SHA-256 一致。
- 失败重试不覆盖旧图，同一错误连续三次立即停止。
- 完成人工评分后，才可把 M5 标记通过并开始 M6。
