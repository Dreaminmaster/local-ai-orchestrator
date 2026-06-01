#!/bin/bash
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator - 测试 Claude"
source venv/bin/activate 2>/dev/null || true
python scripts/test_web_ai_claude.py
echo ""
read -n 1 -s -r -p "按任意键退出..."
