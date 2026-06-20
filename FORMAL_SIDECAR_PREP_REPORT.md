# Formal Sidecar Prep Report

Generated: 2026-06-03T00:00:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: v0.2.3 formal sidecar build preparation only. No `tauri build`, no DMG/EXE/MSI, no signing, no notarization, no updater, no live Claude, and no provider live tests were run.

## Host Target Triple

Rust was read through the existing FlyEnv Rust path for this command only:

`/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin`

`rustc -vV` result:

- rustc: `1.96.0`
- host target: `x86_64-apple-darwin`

Plain shell Rust was not installed or changed.

## Sidecar Binary Naming Rule

Added:

`scripts/prepare_tauri_sidecar_binary.py`

Behavior:

- checks `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`
- reads `rustc -vV`
- copies the prototype binary to `local-ai-orchestrator-backend-<target-triple>`
- for this machine: `local-ai-orchestrator-backend-x86_64-apple-darwin`
- does not build Tauri
- generated sidecar binaries are ignored by `.gitignore`

The generated binary remains local build output and should not be committed.

## ExternalBin Prep

Updated:

`apps/desktop/src-tauri/tauri.conf.json`

Current state:

- `bundle.active=false`
- `bundle.targets=[]`
- `bundle.externalBin=[]`

Formal build target later:

```json
"externalBin": [
  "bin/local-ai-orchestrator-backend"
]
```

Tauri should resolve the target-triple suffixed binary in `src-tauri/bin/`. This preparation intentionally avoids enabling bundle output.

## Runtime Paths Design

Added:

`backend/runtime_paths.py`

Runtime modes:

- dev: project-local `runtime/` and `.playwright-browsers/`
- installed: user app data
- custom: explicit CLI overrides

Installed app data model:

- macOS: `~/Library/Application Support/Local AI Orchestrator/`
- Windows: `%APPDATA%/Local AI Orchestrator/`
- Linux: `~/.local/share/local-ai-orchestrator/`

Managed directories:

- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `runtime/logs/`
- `runtime/tasks/`
- `playwright-browsers/` in installed mode
- `settings.json`

The runtime is not placed inside the App Bundle.

## Settings.json Design

Added:

`backend/settings_store.py`

Default settings include:

- LM Studio endpoint
- Ollama endpoint
- Playwright browsers path
- External AI enabled/status fields for Claude and ChatGPT
- Authorization defaults

Rules:

- creates `settings.json` if missing
- does not store plaintext API keys or secret-like keys
- `.env` remains supported as a dev fallback
- future secure storage remains out of scope

## Playwright Provisioning Status

Added:

`GET /api/playwright/status`

Response includes:

- `configured_path`
- `exists`
- `chromium_found`
- `recommended_action`
- `auto_download=false`

Frontend now shows a project-browser status section. If Chromium is missing, it displays:

- `需要安装项目专用浏览器`
- `以后下载`

No automatic browser download was implemented.

## Capability Review

Current:

`apps/desktop/src-tauri/capabilities/default.json`

Permissions:

- `core:default`

Not present:

- arbitrary shell execution
- broad filesystem access
- Chrome/Safari automation
- Apple Events automation

Future formal sidecar permissions should remain limited to the bundled sidecar path and must not expose arbitrary commands.

## Why Not Tauri Build Yet

Still intentionally missing:

- formal `bundle.active=true`
- signed/notarized macOS bundle
- Windows signing
- updater
- installed runtime migration UI
- settings UI
- Playwright browser provisioning flow
- crash log/diagnostic UX
- port conflict UI for installed users

Therefore this stage is build prep only, not installer production.

## Next Step Before Tauri Build Smoke

After explicit confirmation:

1. Run `scripts/prepare_tauri_sidecar_binary.py`.
2. Confirm target-triple binary exists locally and is ignored.
3. Temporarily enable externalBin for a controlled local `tauri build` smoke only.
4. Do not sign, notarize, DMG, MSI, EXE, or updater.
5. Verify runtime still writes to user-writable locations and not the App Bundle.

## Non-Live Validation

Completed:

- `.build-venv/bin/python scripts/health_check.py`: PASS.
- `.build-venv/bin/python scripts/beta_validation.py`: PASS, live Claude skipped.
- `node --check frontend/app.js`: PASS.
- `.build-venv/bin/python -m unittest tests/test_runtime_paths_settings_playwright.py`: PASS, 5 tests.

No live Claude run and no provider live tests were performed.

## Build Smoke Follow-up

Generated: 2026-06-03T01:30:00+08:00

Controlled Tauri build smoke was attempted after this prep.

Resolved:

- `prepare_tauri_sidecar_binary.py` now supports explicit `--target`, `--auto`, and `--all-macos`.
- This machine requires `aarch64-apple-darwin` for Tauri bundling even though FlyEnv Rust reports `x86_64-apple-darwin`.
- `apps/desktop/src-tauri/src/main.rs` now contains minimal sidecar lifecycle code without adding a shell plugin.
- `frontend/app.js` points Tauri packaged UI API calls to `http://localhost:8422`.
- `npm run build` successfully generated a local unsigned `.app`.

Still partial:

- `/api/health` blocking LM Studio probes were cached and shortened
- packaged smoke now uses a Python HTTP probe with hard timeouts
- UI readiness marker and `/api/ui-ready` were added
- Rust lifecycle logging and app-owned PID shutdown were added
- normal app quit cleanup passed in the latest controlled smoke
- bundled PyInstaller onefile sidecar did not reach Uvicorn within 180 seconds in the latest run
- WebView readiness remains blocked by sidecar startup reliability

See:

`TAURI_BUILD_SMOKE_REPORT.md`

## Onedir Packaged Startup Follow-up

Generated: 2026-06-03

The target-triple onefile externalBin is sufficient for Tauri bundling, but its
packaged startup is not reliable enough for the current prototype. The onefile
process could exist without reaching the Python entry point or Uvicorn within
180 seconds, and its log remained empty.

The onedir diagnostic strategy intentionally does not copy only the executable
into a target-triple externalBin name. An onedir executable depends on the
adjacent collected files. For this smoke, the packaged Rust launcher used the
workspace-known path:

```text
apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-dir/local-ai-orchestrator-backend
```

Results:

- onedir direct startup: PASS
- onedir direct `/api/health`: PASS
- packaged Rust launcher selected `onedir_dev_known_path`: PASS
- packaged sidecar entered Uvicorn: PASS
- packaged `/api/health`: PASS
- packaged sidecar cleanup: PASS
- UI readiness marker: not confirmed

This proves the backend sidecar runtime path, but it is not yet the final formal
bundle layout. A later build-prep step must decide how the full onedir tree is
placed in App resources and how the Rust launcher resolves that installed
resource path.

## Packaged Runtime Smoke Pass

Generated: 2026-06-03

The remaining WebView readiness issue was caused by navigating the packaged
WebView away from Tauri `frontendDist` to the frozen backend root. The backend
does not package frontend files, so that root returned `404`.

The packaged app now keeps the Tauri bundled frontend and uses localhost only
for API calls.

Final controlled smoke:

- build: PASS
- onedir sidecar: PASS
- backend health: PASS
- WebView created: PASS
- UI auto-readiness: PASS
- sidecar shutdown: PASS
- port residue: none
- overall runtime smoke: PASS

The project can proceed to unsigned macOS app prototype planning. Formal onedir
resource bundling, DMG, signing, notarization, updater, and release workflows
remain intentionally out of scope.
