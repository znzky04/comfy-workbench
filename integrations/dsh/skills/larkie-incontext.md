---
name: larkie-incontext
description: 使用 Anima in-context 参考编码保持拉琪身份特征。
---

# Larkie In-Context（运行前必读）

此工作流需要 `AnimaRefEncode`、`AnimaInContextApply` 和 `anima-incontext-character.safetensors`。缺少任一依赖时立即报告，不自动安装。

当前 ComfyUI 0.42.3 的注意力接口会传入 `preferred_attention`。如果采样时报
`ref_attn_op() got an unexpected keyword argument 'preferred_attention'`，不要重复提交；先阅读
`docs/M5_DSH_HANDOFF.md`，在用户手动关闭 Desktop 后应用项目内版本化兼容补丁
`integrations/dsh/patches/comfyui-anima-incontext-comfyui-0.42.3.diff`，再由用户手动重开 Desktop。
不得静默更新全部自定义节点，也不得在 Desktop 运行时直接改加载中的节点代码。

必须提供拉琪参考图，并检查月白发、少量香槟金挑染、幽蓝羽翼、简洁金色星环和成熟少女比例。宽高参数会同时应用到参考编码与目标 latent。

输出只保存在 ComfyUI 权威图库；任何视觉验收失败的图片仍然保留。
