#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright-browsers"

echo "🧠 Local AI Orchestrator — macOS/Linux Setup (Portable)"
echo "=========================================================="
echo "  Playwright dir: $PLAYWRIGHT_BROWSERS_PATH"
echo ""

# 1. Python check
if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Install from: https://www.python.org/downloads/"
  exit 1
fi
echo "✅ python3 $(python3 --version)"

# 2. Create venv
if [ ! -d "$PROJECT_ROOT/venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv "$PROJECT_ROOT/venv"
fi
echo "✅ venv ready"

# 3. Install requirements
echo "📦 Installing Python dependencies..."
"$PROJECT_ROOT/venv/bin/pip" install --upgrade pip -q
"$PROJECT_ROOT/venv/bin/pip" install -r "$PROJECT_ROOT/requirements.txt" -q
echo "✅ requirements installed"

# 4. Copy .env if missing
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo "📝 .env created from .env.example (edit to configure LM Studio/Ollama)"
fi
echo "✅ .env exists"

# 5. Install Playwright chromium to project-local dir
echo "🌐 Installing Playwright Chromium to $PLAYWRIGHT_BROWSERS_PATH ..."
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"
"$PROJECT_ROOT/venv/bin/playwright" install chromium 2>/dev/null || \
  echo "⚠️  Playwright Chromium install skipped (optional for Web AI). Install manually: PLAYWRIGHT_BROWSERS_PATH=.playwright-browsers playwright install chromium"
echo "✅ Playwright check done"

# 6. Create runtime dirs
mkdir -p "$PROJECT_ROOT/runtime/evidence" "$PROJECT_ROOT/runtime/tasks" "$PROJECT_ROOT/runtime/test_reports"
echo "✅ runtime directories ready"

echo ""
echo "============================================="
echo "✅ Setup complete!"
echo ""
echo "Next:"
echo "  ./scripts/start_local.sh"
echo "  Then open http://localhost:8422"
echo ""
echo "Optional:"
echo "  python scripts/init_web_ai_profile.py --provider chatgpt"
