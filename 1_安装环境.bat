@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 安装环境
if not exist "scripts\local_setup_windows.ps1" (
  echo 找不到 scripts\local_setup_windows.ps1
  pause
  exit /b 1
)
powershell -ExecutionPolicy Bypass -File scripts\local_setup_windows.ps1
echo 安装完成。下一步请双击 2_启动项目.bat
pause
