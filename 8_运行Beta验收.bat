@echo off
setlocal
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
set "PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%\.playwright-browsers"
set "PIP_CACHE_DIR=%PROJECT_ROOT%\runtime\pip_cache"
set "TMP=%PROJECT_ROOT%\runtime\tmp"
set "TEMP=%PROJECT_ROOT%\runtime\tmp"
set "PYTHONPATH=%PROJECT_ROOT%"

set "PY=%PROJECT_ROOT%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" scripts\beta_validation.py
echo.
echo Beta 验收完成，报告：%PROJECT_ROOT%\BETA_VALIDATION_REPORT.md
pause
