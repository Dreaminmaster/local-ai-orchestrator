@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 启动项目
if not exist venv (
  echo 未检测到 venv，请先双击 1_安装环境.bat
  pause
  exit /b 1
)
call venv\Scriptsctivate.bat
start http://localhost:8422
python -m backend.main
pause
