# ComfyUI Desktop 安全更新流程

本项目从不代替用户启动、停止或更新 ComfyUI。更新失败若出现 `aimdo.dll 拒绝访问 (os error 5)`，通常表示 Python/ComfyUI 仍占用该 DLL。

1. 保存工作流并在 ComfyUI Desktop 中正常退出。
2. 确认 `http://127.0.0.1:8188/system_stats` 已无法连接。
3. 在任务管理器确认没有属于该工作区的 `python.exe ... main.py`。
4. 仅当上述两项都确认后，在 Desktop 更新界面重试。
5. 更新完成后由用户重新打开 Desktop。
6. 在项目中运行 `comfy-demo doctor` 和 `comfy-demo workflow validate --all --remote`。

只读检查示例：

```powershell
Get-NetTCPConnection -LocalPort 8188 -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -like '*ComfyUI*main.py*'
} | Select-Object ProcessId, Name, CommandLine
```

这些命令只检查占用，不结束进程。若仍有进程，由用户在 Desktop 或任务管理器中确认后处理。
