@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=%cd%\.playwright-browsers
echo Local AI Orchestrator - 初始化 ChatGPT 登录
if exist venv\Scriptsctivate.bat call venv\Scriptsctivate.bat
python scripts\init_web_ai_profile.py --provider chatgpt
pause
