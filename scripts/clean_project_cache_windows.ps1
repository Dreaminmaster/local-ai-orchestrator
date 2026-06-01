# Clean project cache — portable mode
# NEVER deletes: system Playwright paths, Codex/Claude dirs, user profiles
# ONLY deletes: project-local runtime + .playwright-browsers + python cache

$ProjectRoot = $PSScriptRoot
$items = @(
    "$ProjectRoot\.playwright-browsers",
    "$ProjectRoot\runtime",
    "$ProjectRoot\.pytest_cache"
)

Write-Host "🧹 Local AI Orchestrator - 清理项目缓存 (便携模式)" -ForegroundColor Cyan
Write-Host "  只删除项目目录内的文件，不碰系统路径。"
Write-Host ""
Write-Host "将删除:"
foreach ($item in $items) {
    if (Test-Path $item) { Write-Host "  $item" }
}
Write-Host ""
Write-Host "不会删除: venv / .env / src / ~/.xxx / %LOCALAPPDATA%"
Write-Host ""

$confirm = Read-Host "确认清理？[y/N]"
if ($confirm -ne "y") { Write-Host "取消。"; Read-Host "按任意键退出..."; exit }

foreach ($item in $items) {
    if (Test-Path $item) { Remove-Item -Recurse -Force $item; Write-Host "  ✅ 已删除: $item" }
}
# Clean __pycache__ in project
Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ 清理完成"

$deep = Read-Host "深度清理（删除 venv 和 .env）？[y/N]"
if ($deep -eq "y") {
    if (Test-Path "$ProjectRoot\venv") { Remove-Item -Recurse -Force "$ProjectRoot\venv"; Write-Host "  ✅ venv" }
    if (Test-Path "$ProjectRoot\.env") { Remove-Item -Force "$ProjectRoot\.env"; Write-Host "  ✅ .env" }
}
Read-Host "按任意键退出..."
