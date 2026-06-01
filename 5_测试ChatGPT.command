#!/bin/bash
cd "$(dirname "$0")"
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers"
echo "🧠 Local AI Orchestrator - 测试 ChatGPT"
source venv/bin/activate 2>/dev/null || true
python scripts/test_web_ai_chatgpt.py
echo ""
read -n 1 -s -r -p "按任意键退出..."
