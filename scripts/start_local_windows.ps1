# Local AI Orchestrator — Start (Windows, Portable)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $ProjectRoot ".playwright-browsers"

Write-Host "🧠 Local AI Orchestrator — Starting..." -ForegroundColor Cyan
Write-Host "  Web UI: http://localhost:8422"

if (Test-Path "venv") {
    .\venv\Scripts\Activate.ps1
}

Start-Process "http://localhost:8422"
python -m backend.main
