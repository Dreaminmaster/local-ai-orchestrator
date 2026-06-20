#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HEALTH_URL="http://127.0.0.1:8422/api/health"
BACKEND_MODE="${LOCAL_AI_BACKEND_MODE:-python}"
BINARY_PATH="$SCRIPT_DIR/bin/local-ai-orchestrator-backend"

cd "$PROJECT_ROOT"

export PROJECT_ROOT
export PYTHONPATH="$PROJECT_ROOT"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright-browsers"
export PIP_CACHE_DIR="$PROJECT_ROOT/runtime/pip_cache"
export TMPDIR="$PROJECT_ROOT/runtime/tmp"

mkdir -p "$PROJECT_ROOT/runtime/tmp" "$PROJECT_ROOT/runtime/logs"

health_ok() {
  if command -v curl >/dev/null 2>&1 && curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    return 0
  fi
  python3 - "$HEALTH_URL" >/dev/null 2>&1 <<'PY'
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=2) as response:
    raise SystemExit(0 if response.status == 200 else 1)
PY
}

port_occupied() {
  lsof -nP -iTCP:8422 -sTCP:LISTEN >/dev/null 2>&1
}

for _ in $(seq 1 10); do
  if health_ok; then
    echo "[desktop] backend already healthy at $HEALTH_URL"
    while true; do sleep 3600; done
  fi
  sleep 0.2
done

if port_occupied; then
  echo "[desktop] port 8422 is already occupied but $HEALTH_URL is not healthy; not starting a duplicate backend" >&2
  lsof -nP -iTCP:8422 -sTCP:LISTEN >&2 || true
  while true; do sleep 3600; done
fi

if health_ok; then
  echo "[desktop] backend already healthy at $HEALTH_URL"
  while true; do sleep 3600; done
fi

if [ "$BACKEND_MODE" = "binary" ]; then
  if [ ! -x "$BINARY_PATH" ]; then
    echo "[desktop] backend binary not found: $BINARY_PATH" >&2
    echo "[desktop] run scripts/build_backend_binary.py after installing PyInstaller in an approved venv" >&2
    exit 2
  fi
  echo "[desktop] starting backend binary: $BINARY_PATH"
  "$BINARY_PATH" \
    --host 127.0.0.1 \
    --port 8422 \
    --project-root "$PROJECT_ROOT" \
    --runtime-dir "$PROJECT_ROOT/runtime" \
    --playwright-browsers-path "$PROJECT_ROOT/.playwright-browsers" \
    > "$PROJECT_ROOT/runtime/logs/tauri-backend.log" 2>&1 &
  BACKEND_PID=$!
elif [ "$BACKEND_MODE" = "python" ]; then
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
else
  echo "[desktop] unsupported LOCAL_AI_BACKEND_MODE=$BACKEND_MODE; expected python or binary" >&2
  exit 2
fi

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "[desktop] stopping backend pid $BACKEND_PID"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 80); do
  if health_ok; then
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
