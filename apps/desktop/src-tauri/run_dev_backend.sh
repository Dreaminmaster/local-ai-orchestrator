#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HEALTH_URL="http://127.0.0.1:8422/api/health"

cd "$PROJECT_ROOT"

export PROJECT_ROOT
export PYTHONPATH="$PROJECT_ROOT"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright-browsers"
export PIP_CACHE_DIR="$PROJECT_ROOT/runtime/pip_cache"
export TMPDIR="$PROJECT_ROOT/runtime/tmp"

mkdir -p "$PROJECT_ROOT/runtime/tmp" "$PROJECT_ROOT/runtime/logs"

if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
  echo "[desktop] backend already healthy at $HEALTH_URL"
  while true; do sleep 3600; done
fi

if [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
  PY="$PROJECT_ROOT/venv/bin/python"
elif [ -x "/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python" ]; then
  PY="/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python"
  echo "[desktop] using old success venv for dev shell: $PY"
else
  echo "[desktop] Python venv not found. Create project venv separately; this script will not install dependencies." >&2
  exit 2
fi

echo "[desktop] starting backend with $PY run.py"
"$PY" run.py > "$PROJECT_ROOT/runtime/logs/tauri-backend.log" 2>&1 &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "[desktop] stopping backend pid $BACKEND_PID"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 80); do
  if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "[desktop] backend healthy"
    wait "$BACKEND_PID"
    exit $?
  fi
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "[desktop] backend exited early; see runtime/logs/tauri-backend.log" >&2
    exit 1
  fi
  sleep 0.5
done

echo "[desktop] backend did not become healthy; see runtime/logs/tauri-backend.log" >&2
exit 1
