#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator - 安装环境"
echo "当前目录: $(pwd)"
echo ""
if [ ! -f "scripts/local_setup_mac.sh" ]; then
  echo "❌ 找不到 scripts/local_setup_mac.sh，请确认你在项目根目录运行。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 1
fi
chmod +x scripts/local_setup_mac.sh
bash scripts/local_setup_mac.sh
echo ""
echo "✅ 安装完成。下一步请双击 2_启动项目.command"
read -n 1 -s -r -p "按任意键退出..."
