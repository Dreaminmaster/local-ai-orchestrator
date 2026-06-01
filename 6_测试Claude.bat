@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 测试 Claude
if exist venv\Scriptsctivate.bat call venv\Scriptsctivate.bat
python scripts	est_web_ai_claude.py
pause
