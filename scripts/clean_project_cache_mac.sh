#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "🧹 Local AI Orchestrator - 清理项目缓存"
echo ""

ITEMS=("runtime/" ".playwright-browsers/" ".pytest_cache/")
echo "将删除:"
for item in "${ITEMS[@]}"; do
  test -e "$item" && echo "  $item"
done
echo ""
echo "不会删除: venv .env src/ backend/ frontend/"
echo ""

read -p "确认清理？[y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "取消。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 0
fi

for item in "${ITEMS[@]}"; do
  test -e "$item" && rm -rf "$item" && echo "  ✅ 已删除: $item"
done

# Also clean __pycache__
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; true
echo ""
echo "✅ 清理完成。"

read -p "是否深度清理（删除 venv 和 .env）？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf venv .env && echo "  ✅ 已删除 venv 和 .env"
fi

read -n 1 -s -r -p "按任意键退出..."
