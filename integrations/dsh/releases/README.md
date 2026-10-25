# DSH 本地产物

ZIP 文件由 `.gitignore` 排除，保留在本机，不把二进制包提交到仓库。

| 文件 | 用途 | SHA-256 |
|---|---|---|
| `legacy-main-anima-backup-20261025.zip` | 导入新版前的旧“主Anima”回滚备份 | `57a4f630b45b59f9195f6c9a07edae8235e94b7e375d12a7592ac8ea6c54391a` |
| `comfyui-demo-dsh-presets-v0.1.0.zip` | 5 条正式工作流及技能包 | `8ba9edf4faccc1af04549832486153ead149293747438b02bd838ebd26ee2a45` |
| `comfyui-demo-dsh-presets-v0.1.1.zip` | 增加 ComfyUI 0.42.3 in-context 兼容故障指引的交接版 | `6399fd021dd48c0595d2da7b4d5b9e9e2995958f13bdcf359fadfaa2e1828f3c` |
| `comfyui-demo-dsh-presets-v0.1.2.zip` | 5 条工作流暴露唯一 output_prefix 参数 | `8c185c8e73dba1efa83626c3dbbc8a477bd142c7ff4ef4b56884ca77db0f70af` |

所有包均已通过项目 `verify_bundle` 离线校验。DSH 后续使用 v0.1.2；重新导入会创建新工作流，不覆盖旧记录。v0.1.2 还通过官方插件 applyWorkflowParameters 的 5/5 参数契约验证，本轮未启动 DSH 进行 UI 重导入。
