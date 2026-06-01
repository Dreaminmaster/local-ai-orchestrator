#!/bin/bash
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator - 初始化 ChatGPT 登录"
echo "浏览器将打开 ChatGPT 网页，请手动登录。"
echo "登录完成后回到此窗口。"
source venv/bin/activate 2>/dev/null || true
python scripts/init_web_ai_profile.py --provider chatgpt
read -n 1 -s -r -p "按任意键退出..."
