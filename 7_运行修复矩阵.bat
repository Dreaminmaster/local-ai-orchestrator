@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local AI Orchestrator - 运行修复矩阵
if exist venv\Scriptsctivate.bat call venv\Scriptsctivate.bat
python scripts\e2e_agent_driven_repair_matrix.py
pause
