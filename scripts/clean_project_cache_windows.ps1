Write-Host "🧹 Local AI Orchestrator - 清理项目缓存" -ForegroundColor Cyan
Write-Host ""
Write-Host "将删除: runtime / .playwright-browsers / __pycache__"
Write-Host "不会删除: venv / .env / src"
Write-Host ""

$confirm = Read-Host "确认清理？[y/N]"
if ($confirm -ne "y") { Write-Host "取消。"; pause; exit }

if (Test-Path runtime) { Remove-Item -Recurse -Force runtime; Write-Host "  ✅ runtime" }
if (Test-Path .playwright-browsers) { Remove-Item -Recurse -Force .playwright-browsers; Write-Host "  ✅ .playwright-browsers" }
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ 清理完成"

$deep = Read-Host "深度清理（删除 venv 和 .env）？[y/N]"
if ($deep -eq "y") {
  if (Test-Path venv) { Remove-Item -Recurse -Force venv; Write-Host "  ✅ venv" }
  if (Test-Path .env) { Remove-Item -Force .env; Write-Host "  ✅ .env" }
}
pause
