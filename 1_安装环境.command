#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator - 安装环境 (便携模式)"
echo "当前目录: $(pwd)"
echo ""

# Set Playwright to project-local dir
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers"

# First run doctor
echo "── 检查当前状态 ──"
python3 scripts/doctor.py
echo ""

# Ask user
read -p "是否补装缺失项？[y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "跳过安装。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 0
fi

# Install missing
python3 scripts/install_missing.py
echo ""
read -n 1 -s -r -p "按任意键退出..."
