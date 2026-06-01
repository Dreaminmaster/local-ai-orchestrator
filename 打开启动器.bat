@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=%cd%\.playwright-browsers
if exist venv\Scriptsctivate.bat call venv\Scriptsctivate.bat
python launcher.py
pause
