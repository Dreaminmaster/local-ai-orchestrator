@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 运行体检
if exist venv\Scriptsctivate.bat call venv\Scriptsctivate.bat
python scripts\doctor.py
pause
