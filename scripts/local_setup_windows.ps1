# Local AI Orchestrator — Windows Setup
Write-Host "🧠 Local AI Orchestrator — Windows Setup" -ForegroundColor Cyan
Write-Host "============================================="

# 1. Python check
try {
  $v = python --version 2>&1
  Write-Host "✅ $v"
} catch {
  Write-Host "❌ python not found. Install from: https://www.python.org/downloads/" -ForegroundColor Red
  exit 1
}

# 2. Create venv
if (-not (Test-Path "venv")) {
  Write-Host "📦 Creating virtual environment..."
  python -m venv venv
}
Write-Host "✅ venv ready"

# 3. Install requirements
Write-Host "📦 Installing Python dependencies..."
.\venv\Scripts\pip install --upgrade pip -q
.\venv\Scripts\pip install -r requirements.txt -q
Write-Host "✅ requirements installed"

# 4. Copy .env if missing
if (-not (Test-Path ".env")) {
  Copy-Item .env.example .env
  Write-Host "📝 .env created from .env.example"
}
Write-Host "✅ .env exists"

# 5. Install Playwright chromium
Write-Host "🌐 Checking Playwright..."
try {
  .\venv\Scripts\playwright install chromium 2>$null
  Write-Host "✅ Playwright ready"
} catch {
  Write-Host "⚠️  Playwright install skipped (optional)"
}

# 6. Runtime dirs
New-Item -ItemType Directory -Force -Path runtime/evidence, runtime/tasks, runtime/test_reports | Out-Null
Write-Host "✅ runtime directories ready"

Write-Host ""
Write-Host "✅ Setup complete! Next:" -ForegroundColor Green
Write-Host "  .\scripts\start_local_windows.ps1"
Write-Host "  Then open http://localhost:8422"
