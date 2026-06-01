# Local AI Orchestrator — Windows Setup (Portable)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $ProjectRoot ".playwright-browsers"

Write-Host "🧠 Local AI Orchestrator — Windows Setup (Portable)" -ForegroundColor Cyan
Write-Host "======================================================"
Write-Host "  Project root: $ProjectRoot"
Write-Host "  Playwright dir: $env:PLAYWRIGHT_BROWSERS_PATH"
Write-Host ""

# 1. Python check
try {
    $v = python --version 2>&1
    Write-Host "✅ $v"
} catch {
    Write-Host "❌ python not found. Install from: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 2. Create venv
if (-not (Test-Path "$ProjectRoot\venv")) {
    Write-Host "📦 Creating virtual environment..."
    python -m venv "$ProjectRoot\venv"
}
Write-Host "✅ venv ready"

# 3. Install requirements
Write-Host "📦 Installing Python dependencies..."
& "$ProjectRoot\venv\Scripts\pip" install --upgrade pip -q
& "$ProjectRoot\venv\Scripts\pip" install -r "$ProjectRoot\requirements.txt" -q
Write-Host "✅ requirements installed"

# 4. Copy .env if missing
if (-not (Test-Path "$ProjectRoot\.env")) {
    Copy-Item "$ProjectRoot\.env.example" "$ProjectRoot\.env"
    Write-Host "📝 .env created from .env.example"
}
Write-Host "✅ .env exists"

# 5. Install Playwright chromium to project-local dir
Write-Host "🌐 Installing Playwright Chromium to $env:PLAYWRIGHT_BROWSERS_PATH ..."
New-Item -ItemType Directory -Force -Path "$env:PLAYWRIGHT_BROWSERS_PATH" | Out-Null
try {
    & "$ProjectRoot\venv\Scripts\playwright" install chromium 2>$null
    Write-Host "✅ Playwright Chromium ready"
} catch {
    Write-Host "⚠️  Playwright install skipped. Install manually: set PLAYWRIGHT_BROWSERS_PATH=.playwright-browsers && playwright install chromium"
}

# 6. Runtime dirs
New-Item -ItemType Directory -Force -Path "$ProjectRoot\runtime\evidence", "$ProjectRoot\runtime\tasks", "$ProjectRoot\runtime\test_reports" | Out-Null
Write-Host "✅ runtime directories ready"

Write-Host ""
Write-Host "✅ Setup complete! Next:" -ForegroundColor Green
Write-Host "  .\scripts\start_local_windows.ps1"
Write-Host "  Then open http://localhost:8422"
