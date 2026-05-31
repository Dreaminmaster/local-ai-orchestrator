#!/usr/bin/env bash
set -eu

echo "🧠 Local AI Orchestrator — macOS/Linux Setup"
echo "============================================="

# 1. Python check
if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Install from: https://www.python.org/downloads/"
  exit 1
fi
echo "✅ python3 $(python3 --version)"

# 2. Create venv
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi
echo "✅ venv ready"

# 3. Install requirements
echo "📦 Installing Python dependencies..."
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q
echo "✅ requirements installed"

# 4. Copy .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "📝 .env created from .env.example (edit to configure LM Studio/Ollama)"
fi
echo "✅ .env exists"

# 5. Install Playwright chromium
if ! ./venv/bin/python -c "from playwright.sync_api import sync_playwright; sync_playwright().__enter__().chromium.launch(); exit(0)" 2>/dev/null; then
  echo "🌐 Installing Playwright chromium..."
  ./venv/bin/playwright install chromium 2>/dev/null || echo "⚠️  Playwright install skipped (optional for Web AI)"
fi
echo "✅ Playwright check done"

# 6. Create runtime dirs
mkdir -p runtime/evidence runtime/tasks runtime/test_reports
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
