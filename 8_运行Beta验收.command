#!/bin/zsh
set -e
cd "$(dirname "$0")"
export PROJECT_ROOT="$PWD"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright-browsers"
export PIP_CACHE_DIR="$PROJECT_ROOT/runtime/pip_cache"
export TMPDIR="$PROJECT_ROOT/runtime/tmp"
export PYTHONPATH="$PROJECT_ROOT"

PY="$PROJECT_ROOT/venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3)"
fi

"$PY" scripts/beta_validation.py
echo
echo "Beta 验收完成，报告：$PROJECT_ROOT/BETA_VALIDATION_REPORT.md"
read "?按回车退出..."
