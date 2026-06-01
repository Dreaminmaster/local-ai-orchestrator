#!/bin/bash
cd "$(dirname "$0")"
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers"
echo "🧠 Local AI Orchestrator - 运行修复矩阵"
source venv/bin/activate 2>/dev/null || true
python scripts/e2e_agent_driven_repair_matrix.py
echo ""
read -n 1 -s -r -p "按任意键退出..."
