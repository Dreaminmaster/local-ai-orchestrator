#!/bin/bash
set -eu
cd "$(dirname "$0")"
echo "🧠 Local AI Orchestrator — Starting..."
echo "  Web UI: http://localhost:8422"
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers"
if [ -d "venv" ]; then
  source venv/bin/activate
fi
if command -v open &>/dev/null; then
  (sleep 2 && open http://localhost:8422) &
elif command -v xdg-open &>/dev/null; then
  (sleep 2 && xdg-open http://localhost:8422) &
fi
python -m backend.main
