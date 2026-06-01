# Local AI Orchestrator — Start (Windows)
Write-Host "🧠 Local AI Orchestrator — Starting..." -ForegroundColor Cyan
Write-Host "  Web UI: http://localhost:8422"
$env:PLAYWRIGHT_BROWSERS_PATH = "$pwd\.playwright-browsers"
if (Test-Path "venv") { .\venv\Scripts\Activate.ps1 }
Start-Process "http://localhost:8422"
python -m backend.main
