#!/bin/bash
# Clean project cache — portable mode
# NEVER deletes: system Playwright paths, Codex/Claude dirs, user profiles
# ONLY deletes: project-local .playwright-browsers/ runtime/ .pytest_cache/ __pycache__/
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
echo "🧹 Local AI Orchestrator - 清理项目缓存 (便携模式)"
echo "  只删除项目目录内的文件，不碰系统路径。"
echo ""

ITEMS=(".playwright-browsers/" "runtime/" ".pytest_cache/")
echo "将删除:"
for item in "${ITEMS[@]}"; do
  test -e "$item" && echo "  $item"
done
echo ""
echo "不会删除: venv .env src/ backend/ frontend/"
echo "禁止删除: ~/Library/Caches/ms-playwright ~/.playwright 等系统路径"
echo ""

read -n 1 -s -r -p "确认清理？[y/N] "
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "取消。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 0
fi

for item in "${ITEMS[@]}"; do
  test -e "$item" && rm -rf "$item" && echo "  ✅ 已删除: $item"
done
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
echo "✅ 清理完成"

read -n 1 -s -r -p "深度清理（删除 venv 和 .env）？[y/N] "
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf venv .env && echo "  ✅ 已删除 venv 和 .env"
fi
read -n 1 -s -r -p "按任意键退出..."
