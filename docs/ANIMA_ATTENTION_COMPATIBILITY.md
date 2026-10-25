# Anima in-context 注意力兼容修复

日期：2026-10-25。针对本机 ComfyUI 0.42.5（DSH 交回时版本）。

## 已完成

ComfyUI 的 self-attention 接收 `AttentionTensorContainer`，自定义节点原本直接访问 `.shape`/`.transpose`。第一层 kwargs 补丁仅修复 `preferred_attention` 参数，因此真实采样仍失败。

第二层补丁只改 `make_ref_attn_op`：

- 形状检查通过 `peek()`，保留输入所有权。
- 禁用、中性或序列长度不匹配时，把原容器、原 transformer_options 和关键字参数交回原 attention op。
- 仅在参考偏置分支消费容器，继续使用既有 SDPA 和参考 key bias。
- 普通 Tensor 保持兼容，避免把 Tensor.take(index) 错当容器 take()。

修复前用 CPU 测试重现 2 项容器失败；修复后全部 6 项通过。测试直接提取本机核心的真实容器类和 `wrap_attn`，不加载模型或启动服务。

```powershell
& 'E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\.venv\Scripts\python.exe' scripts/check_anima_attention_compat.py
```

## 文件和回滚

外部目标：

```text
E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\custom_nodes\comfyui-anima-incontext\incontext.py
```

本次修改前确认 8188 未监听，也无 main.py。创建备份：

```text
incontext.py.bak-codex-containers-20261025-184155
SHA-256: 5ff9cfa734307ba0b9ff5b6f443bc369312a5982992c016c7cd8a3c64499c233
```

修复后 SHA-256：

```text
ee9b7f3c4d275779ff4717c5bee3024f6e8b6a2deb8d48c4d1a1b8351375e4e3
```

项目内增量补丁（以 DSH 第一层修复后文件为基线）：

```text
integrations/dsh/patches/comfyui-anima-incontext-comfyui-0.42.x-containers.diff
```

已对当前文件通过 `git apply --check --reverse`，确认补丁与实际改动一致。以后节点更新可能覆盖此改动；重新应用前必须先检查内容及补丁适用性。

需要回滚时，先由用户关闭 Desktop，再用上述本次备份恢复。恢复后是 DSH 交回的第一层补丁状态，in-context 仍不可用；原始未补丁文件另有 DSH 的 `incontext.py.bak-20261025-132743`。

## 在线验证结果

用户手动启动 ComfyUI Desktop 0.42.5 后，官方 comfy-mcp 完成预检、异步提交、轮询和输出解析。正式任务完整运行 88.02 秒，接口修复已通过真实 GPU 验证。

```text
job_id: ae92c6ea-f306-4ed7-ad96-38834ff1bd6f
prompt_id: a031443e-c606-42dd-98b4-9b7cf9669b14
manifest: runs/2026/10/ae92c6ea-f306-4ed7-ad96-38834ff1bd6f.json
output: E:\Comfy-Desktop\ComfyUI-Shared\output\comfyui-demo\2026-10-25\larkie-incontext-v1\benchmark_larkie_incontext_ae92c6ea-f306-4ed7-ad96-38834ff1bd6f_240102_1_00001_.png
```

技术完成、视觉不通过：服装更暴露，参考服装与面部身份保持弱，环形星环变为星芒。Codex 视觉评分已写入 manifest，明确不代表用户批准，也不进入公开精选。

8/8 正式任务现均有完成记录、实际输出和评分，覆盖 5/5 工作流；12 个原始画布工作流哈希不变。M5 保持进行中：视觉验收与下述 DSH 命名契约仍待解决；M6/M7 尚未开始。

DSH 狂三已有成功结果，继续保留 `E:\Comfy-Desktop\ComfyUI-Shared\output\anima_00003_.png`。其通道仍使用内置 SaveImage 前缀，尚未满足统一 job 前缀契约；后续需通过受支持的参数/导入方式补齐，不能改写历史路径。
