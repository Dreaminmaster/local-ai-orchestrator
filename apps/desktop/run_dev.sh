#!/usr/bin/env bash
set -euo pipefail

DESKTOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DESKTOP_DIR/../.." && pwd)"
HEALTH_URL="http://127.0.0.1:8422/api/health"

echo "[desktop] project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

missing=0
for cmd in node npm cargo rustc; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[desktop] missing $cmd"
    missing=1
  else
    echo "[desktop] $cmd: $($cmd --version 2>/dev/null | head -1)"
  fi
done

if ! command -v cargo-tauri >/dev/null 2>&1 && ! command -v tauri >/dev/null 2>&1 && [ ! -x "$DESKTOP_DIR/node_modules/.bin/tauri" ]; then
  echo "[desktop] missing Tauri CLI. Install it outside this script, for example as a project dev dependency with npm install, or cargo install tauri-cli."
  missing=1
fi

if [ "$missing" -ne 0 ]; then
  echo "[desktop] environment incomplete; no global install was attempted."
  exit 2
fi

if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
  echo "[desktop] backend already healthy: $HEALTH_URL"
else
  echo "[desktop] backend not healthy yet. Tauri beforeDevCommand will run src-tauri/run_dev_backend.sh."
fi

cd "$DESKTOP_DIR"
echo "[desktop] starting Tauri dev shell at http://127.0.0.1:8422"
npm run dev
