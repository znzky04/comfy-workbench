# DSH 本地产物

ZIP 文件由 `.gitignore` 排除，保留在本机，不把二进制包提交到仓库。

| 文件 | 用途 | SHA-256 |
|---|---|---|
| `legacy-main-anima-backup-20261025.zip` | 导入新版前的旧“主Anima”回滚备份 | `57a4f630b45b59f9195f6c9a07edae8235e94b7e375d12a7592ac8ea6c54391a` |
| `comfyui-demo-dsh-presets-v0.1.0.zip` | 5 条正式工作流及技能包 | `8ba9edf4faccc1af04549832486153ead149293747438b02bd838ebd26ee2a45` |
| `comfyui-demo-dsh-presets-v0.1.1.zip` | 增加 ComfyUI 0.42.3 in-context 兼容故障指引的交接版 | `6399fd021dd48c0595d2da7b4d5b9e9e2995958f13bdcf359fadfaa2e1828f3c` |

两个新版包均已通过项目 `verify_bundle` 离线校验。DSH 后续使用 v0.1.1；导入测试必须在 DSH UI 中由用户执行，导入会创建新工作流，不覆盖旧记录。
