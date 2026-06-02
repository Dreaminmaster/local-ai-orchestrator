$ErrorActionPreference = "Stop"

$DesktopDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $DesktopDir "..\..")
$HealthUrl = "http://127.0.0.1:8422/api/health"

Write-Host "[desktop] project root: $ProjectRoot"
Set-Location $ProjectRoot

$missing = $false
foreach ($cmd in @("node", "npm", "cargo", "rustc")) {
  $found = Get-Command $cmd -ErrorAction SilentlyContinue
  if (-not $found) {
    Write-Host "[desktop] missing $cmd"
    $missing = $true
  } else {
    Write-Host "[desktop] $cmd: $(& $cmd --version)"
  }
}

$tauriLocal = Join-Path $DesktopDir "node_modules\.bin\tauri.cmd"
$tauriFound = (Get-Command "cargo-tauri" -ErrorAction SilentlyContinue) -or (Get-Command "tauri" -ErrorAction SilentlyContinue) -or (Test-Path $tauriLocal)
if (-not $tauriFound) {
  Write-Host "[desktop] missing Tauri CLI. Install it outside this script, for example as a project dev dependency with npm install, or cargo install tauri-cli."
  $missing = $true
}

if ($missing) {
  Write-Host "[desktop] environment incomplete; no global install was attempted."
  exit 2
}

try {
  Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 | Out-Null
  Write-Host "[desktop] backend already healthy: $HealthUrl"
} catch {
  Write-Host "[desktop] backend not healthy yet. Tauri beforeDevCommand will run src-tauri/run_dev_backend.sh on Unix; configure an equivalent Windows backend command before Windows dev."
}

Set-Location $DesktopDir
Write-Host "[desktop] starting Tauri dev shell at http://127.0.0.1:8422"
npm run dev
