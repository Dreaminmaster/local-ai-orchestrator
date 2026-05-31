# Local AI Orchestrator — Start (Windows)
Write-Host "🧠 Local AI Orchestrator — Starting..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Web UI: http://localhost:8422"
Write-Host ""

if (Test-Path "venv") {
  .\venv\Scripts\Activate.ps1
}

Start-Process "http://localhost:8422"
python -m backend.main
