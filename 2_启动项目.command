#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator - 启动项目"
echo ""
if [ ! -d "venv" ]; then
  echo "❌ 未检测到 venv，请先双击 1_安装环境.command"
  read -n 1 -s -r -p "按任意键退出..."
  exit 1
fi
source venv/bin/activate
python -m backend.main &
BACKEND_PID=$!
sleep 3
if command -v open &>/dev/null; then
  open http://localhost:8422
else
  echo "请手动打开 http://localhost:8422"
fi
echo ""
echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo "   浏览器应已打开: http://localhost:8422"
echo "   关闭此窗口将停止后端。"
wait $BACKEND_PID
