@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动 Anima 画图台...
start "" "E:\AI\ComfyUI-Workspace\ComfyUI\ComfyUI\.venv\Scripts\python.exe" "%~dp0anima_studio.py"
