---
name: anima-hq-2x
description: 使用 Anima 生成并进行 2 倍精修；显存占用高，运行前必须检查。
---

# Anima HQ 2x（运行前必读）

此流程包含 `UltimateSDUpscale` 与 RealESRGAN，适合已确认构图后的精修，不适合第一轮探索。

1. 先检查 `system_stats` 的可用显存与当前队列。
2. 12 GB 显存环境一次只提交一个 HQ 任务；显存紧张时先降低基础尺寸。
3. seed、steps 与 CFG 同步应用到基础采样和精修节点。
4. 超时或显存不足时保留失败记录，不删除已产生文件。
5. 输出只引用 ComfyUI 权威路径，不复制到项目目录。
