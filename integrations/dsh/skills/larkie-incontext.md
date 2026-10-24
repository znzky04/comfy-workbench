---
name: larkie-incontext
description: 使用 Anima in-context 参考编码保持拉琪身份特征。
---

# Larkie In-Context（运行前必读）

此工作流需要 `AnimaRefEncode`、`AnimaInContextApply` 和 `anima-incontext-character.safetensors`。缺少任一依赖时立即报告，不自动安装。

必须提供拉琪参考图，并检查月白发、少量香槟金挑染、幽蓝羽翼、简洁金色星环和成熟少女比例。宽高参数会同时应用到参考编码与目标 latent。

输出只保存在 ComfyUI 权威图库；任何视觉验收失败的图片仍然保留。
