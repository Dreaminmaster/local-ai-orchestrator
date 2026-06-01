#!/usr/bin/env bash
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright-browsers"

echo "🧠 Local AI Orchestrator — Starting..."
echo "  Web UI: http://localhost:8422"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

if command -v open &>/dev/null; then
  (sleep 2 && open http://localhost:8422) &
elif command -v xdg-open &>/dev/null; then
  (sleep 2 && xdg-open http://localhost:8422) &
fi

python -m backend.main
