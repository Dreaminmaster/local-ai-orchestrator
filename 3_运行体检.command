#!/bin/bash
cd "$(dirname "$0")"
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers"
echo "🧠 Local AI Orchestrator - 运行体检"
source venv/bin/activate 2>/dev/null || true
python3 scripts/doctor.py
echo ""
read -n 1 -s -r -p "按任意键退出..."
