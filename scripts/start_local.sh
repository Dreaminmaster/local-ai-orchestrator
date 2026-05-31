#!/usr/bin/env bash
set -eu

echo "🧠 Local AI Orchestrator — Starting..."
echo ""
echo "  Web UI: http://localhost:8422"
echo ""

# Activate venv
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Open browser after a short delay
if command -v open &>/dev/null; then
  (sleep 2 && open http://localhost:8422) &
elif command -v xdg-open &>/dev/null; then
  (sleep 2 && xdg-open http://localhost:8422) &
fi

python -m backend.main
