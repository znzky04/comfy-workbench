@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 迁移提示：画图台使用项目统一核心，不会启动 ComfyUI Desktop。
"%~dp0.venv\Scripts\comfy-demo.exe" studio
pause
