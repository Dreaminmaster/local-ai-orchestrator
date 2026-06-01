@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 安装环境 (便携模式)
echo 当前目录: %cd%
echo.
set PLAYWRIGHT_BROWSERS_PATH=%cd%\.playwright-browsers
echo -- 检查当前状态 --
python scripts\doctor.py
echo.
set /p CONFIRM=是否补装缺失项？[y/N] 
if /i not "%CONFIRM%"=="y" (
  echo 跳过安装。
  pause
  exit /b 0
)
python scripts\install_missing.py
echo.
pause
