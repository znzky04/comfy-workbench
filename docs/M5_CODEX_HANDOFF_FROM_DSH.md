# M5 交回 Codex（来自 DSH）

日期：2026-10-25
DSH 执行范围：预设导入 → 时崎狂三正式任务 → in-context 兼容补丁应用与验证。按用户指示 **B 方案：保持现状，交回 Codex**。

## 结论

- 时崎狂三 DSH 任务**成功并已评分**，manifest 已补录。
- in-context 兼容补丁**只解决了第一层**（`preferred_attention` 关键字），第二层 `AttentionTensorContainer` 未解包，DSH 额外测试在 KSampler 失败。
- **M5 未通过**，M6/M7 门禁保持锁定。
- 正式 `larkie-incontext` 任务必须由 Codex 通过官方 comfy-mcp 重跑；DSH 的失败记录不算正式任务。

## 一、DSH 已完成

### 预设导入（v0.1.1）

- ZIP：`integrations/dsh/releases/comfyui-demo-dsh-presets-v0.1.1.zip`
- SHA-256：`6399fd021dd48c0595d2da7b4d5b9e9e2995958f13bdcf359fadfaa2e1828f3c`（与预期一致）
- 校验：`comfy-demo dsh verify` → `ok:true, count:5`
- 导入方式：`dsh-comfyui` 插件自身导入接口（`/comfyui/workflows/import/analyze` → `/apply`），未读写私有 `workflows.json`，未改 `node_modules`
- 新增 5 条（新 id，未覆盖旧记录）：

```text
anima.standard.v1      → 8751c2b1-2334-446f-81e1-d66a458d8c5c
anima.hq-2x.v1         → 36223c76-555b-4ad5-ad92-558c8e9f7cf7
animagine.standard.v1  → af2198df-1d38-464e-87ae-d087154228d9
larkie.img2img.v1      → c1508065-2b4f-4881-b44a-5eeeba6d8e8f
larkie.incontext.v1    → 872a4133-9fe3-4d6a-bf27-1f7324e47348
```

旧「主Anima」（`c59d83b5-baee-417c-85b3-b04401c93885`）原样保留，库内共 6 条。v0.1.0 从未导入过库，无覆盖问题。

### 时崎狂三（client=dsh）

| 项 | 值 |
|---|---|
| workflow | `anima.standard.v1`（sha `fb5972fa…686d`，与注册表一致） |
| 参数 | seed `240201` / 832×1216 / 28 步 / CFG 4.5 / denoise 1.0 |
| prompt_id | `31ea2ca0-699f-4629-ab25-fe3dd4f70050` |
| 输出 | `E:\Comfy-Desktop\ComfyUI-Shared\output\anima_00003_.png` |
| manifest | `runs/2026/10/31ea2ca0-699f-4629-ab25-fe3dd4f70050.json`（校验通过） |
| 评分 | 身份 5 / 构图 5 / 人体 4 / 材质 5 / 总体 4 |
| 备注 | 身份特征齐全；脚踝与鞋略简化；露肩吊带袜、姿态偏展示性，未完全达成 nonsexualized 目标；图片已保留 |

## 二、当前文件状态（重要）

| 项 | 值 |
|---|---|
| 目标文件 | `E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\custom_nodes\comfyui-anima-incontext\incontext.py` |
| 当前状态 | **已应用 0.42.3 补丁**（仅 `**kwargs` 透传），13530 字节 |
| 当前 SHA-256 | `5FF9CFA734307BA0B9FF5B6F443BC369312A5982992C016C7CD8A3C64499C233` |
| 改前 SHA-256 | `EDDB9D2E8784F4B4F0ACDBA1887509EBB77EAA78772136908336036D2F14C0FA` |
| 备份 | `incontext.py.bak-20261025-132743`（13069 字节） |
| 补丁文件 | `integrations/dsh/patches/comfyui-anima-incontext-comfyui-0.42.3.diff` |

环境：ComfyUI **0.42.5**（tag `v0.42.5`，2026-10-23），Python 3.13.12，Torch 2.10.0+cu130，RTX 5070 Ti Laptop 12GB。
`comfy/ldm/modules/attention.py` 在 `v0.42.3` 与当前工作区**字节一致**（blob `abed292bf742eb8ea9493e0e6341ca5264efdc8a`），所以本次失败不是版本升级引起。

## 三、阻塞证据

DSH 额外测试（非正式任务）：

| 项 | 值 |
|---|---|
| workflow | `larkie.incontext.v1`（sha `5b31551e…`） |
| prompt_id | `3c705098-09a0-4251-a20a-1edbd91d2c8e` |
| 失败节点 | `23 KSampler` |
| 错误 | `AttributeError: 'AttentionTensorContainer' object has no attribute 'shape'` |
| manifest | `runs/2026/10/3c705098-09a0-4251-a20a-1edbd91d2c8e.json`（`client=dsh`、`benchmark_task_id=null`，不计入 8 个正式任务） |
| 图片 | 无（未生成） |

调用栈关键两行：

```python
# comfy/ldm/modules/attention.py Attention.forward
q, k, v = AttentionTensorContainer(q), AttentionTensorContainer(k), AttentionTensorContainer(v)
...
result = self.attn_op(q, k, v, transformer_options=transformer_options,
                      preferred_attention=self.comfy_attention)
```

`make_ref_attn_op` 返回的 `ref_attn_op` 仍把入参当 Tensor 用（`.shape`、`.transpose`），因此第二个错误在第一层修复后才暴露。

## 四、建议的后续补丁（DSH 未应用，需 Codex 决策）

在同一文件、同一函数内做容器解包，仍保持最小改动：

```python
def ref_attn_op(q_B_S_H_D, k_B_S_H_D, v_B_S_H_D, transformer_options={}, **kwargs):
    peek = lambda t: t.peek() if hasattr(t, "peek") else t
    q_t, k_t, v_t = peek(q_B_S_H_D), peek(k_B_S_H_D), peek(v_B_S_H_D)
    # 形状判断用 q_t/k_t；命中 fallback 时把原容器传回，保留核心容器优化路径
    ...
    # 需要自己算 SDPA 时再 take()
```

要点：

1. 形状判断用 `peek()`（只读，不消费容器）。
2. 命中 fallback 时**传原容器**，让核心 `wrap_attn` 仍能走 `container_function` 优化路径。
3. 只有进入自定义 SDPA 分支时才 `take()`。
4. 建议同时用 `transformer_options["optimized_attention_override"]` 的情况验证一次。

## 五、回滚

用户关闭 Desktop 后：

```powershell
Copy-Item "...\comfyui-anima-incontext\incontext.py.bak-20261025-132743" "...\incontext.py" -Force
```

或 `git apply -R integrations/dsh/patches/comfyui-anima-incontext-comfyui-0.42.3.diff`（在节点目录）。

## 六、Codex 接手清单

1. 复核 `incontext.py` 当前内容与第三节证据。
2. 写容器兼容补丁（建议新版本化文件，例如 `comfyui-anima-incontext-comfyui-0.42.x-containers.diff`），先 `git apply --check`。
3. 由用户手动关闭 Desktop，确认 8188 释放、无 `main.py`，再备份并应用。
4. 语法检查 + 节点内置测试（当前节点目录无测试）。
5. 用户手动重开 Desktop，跑 `comfy-demo doctor` 与远程校验。
6. 用官方 comfy-mcp 跑**正式** `larkie-incontext`（`client=codex`），补录 manifest 并评分。
7. 8 个正式任务齐备、5 条工作流各成功一次后，才可把 M5 标记通过。

纪律：同一错误连续三次停止；不得无改动重复提交；不删除/覆盖任何图片；不改 12 个画布工作流；不在 M5 通过前开发 M6。
