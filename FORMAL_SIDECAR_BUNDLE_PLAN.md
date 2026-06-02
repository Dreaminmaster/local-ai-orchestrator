# Formal Sidecar Bundle Plan

Generated: 2026-06-02T23:35:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: formal sidecar bundle design only. No `tauri build`, no DMG/EXE/MSI, no signing, no notarization, no updater, no live provider tests, and no Playwright browser packaging were performed.

## A. Current Prototype State

Completed:

- PyInstaller prototype binary has been generated locally.
- Prototype binary path: `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`.
- `--version`: PASS.
- `--health-check-only`: PASS.
- direct binary `/api/health`: PASS.
- Tauri dev `LOCAL_AI_BACKEND_MODE=binary`: PASS.
- Tauri WebView loaded the local product UI.
- Existing backend reuse: PASS.
- Closing Tauri stopped only the binary backend it started.
- Final port `8422` cleanup: PASS.

Still not completed:

- No formal Tauri bundle.
- No `bundle.externalBin`.
- No target-triple sidecar naming.
- No installed-app runtime directory migration.
- No DMG/EXE/MSI.
- No signing, notarization, updater, or release pipeline.

## B. Tauri `externalBin` Design

Tauri formal sidecars are normally stored under:

`apps/desktop/src-tauri/bin/`

For formal builds, sidecar binaries should be named with target triples. Recommended names:

- macOS Apple Silicon: `local-ai-orchestrator-backend-aarch64-apple-darwin`
- macOS Intel: `local-ai-orchestrator-backend-x86_64-apple-darwin`
- Windows x64: `local-ai-orchestrator-backend-x86_64-pc-windows-msvc.exe`

The current prototype name:

`local-ai-orchestrator-backend`

is acceptable for dev smoke but not enough for formal cross-target bundle layout.

Future Tauri config sketch:

```json
{
  "bundle": {
    "active": true,
    "externalBin": [
      "bin/local-ai-orchestrator-backend"
    ]
  }
}
```

Before formal build, confirm the exact Tauri v2 target-specific sidecar naming behavior in the active Tauri CLI version. Some flows expect the base path in `externalBin` and locate the target-triple suffixed binary automatically.

Current `tauri.conf.json` is not ready for formal `externalBin`:

- `bundle.active` is `false`.
- `targets` is empty.
- `externalBin` is absent.
- `beforeDevCommand` is dev-only.
- `devUrl` points to `http://127.0.0.1:8422`.

Capability direction:

- Keep `core:default` minimal.
- Do not add broad shell execution permissions.
- If a Tauri shell/process plugin is introduced later, scope it to this sidecar only.
- Prefer Tauri-managed sidecar APIs over arbitrary command execution.

## C. Runtime Directory Design

### Dev Mode

Current dev paths:

- `runtime/`
- `.playwright-browsers/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`

These live under the project directory for portable development.

### Installed App Mode

Installed runtime must move to a user-writable app data location. It must not live inside the `.app` bundle or executable directory.

Recommended installed layout:

macOS:

`~/Library/Application Support/Local AI Orchestrator/`

Windows:

`%APPDATA%\\Local AI Orchestrator\\`

Installed runtime subdirectories:

- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `runtime/tasks/`
- `runtime/tmp/`
- `runtime/logs/`
- `.playwright-browsers/` or `playwright-browsers/`

`.env` should not be bundled into the binary or app. Long-term replacement should be:

- settings UI
- explicit external config file
- per-user app data settings JSON

## D. Playwright Browsers

Current stage:

- Do not automatically package Playwright browsers.
- Continue to use configurable `PLAYWRIGHT_BROWSERS_PATH`.
- Keep browsers outside Codex/system Playwright caches.

Future installed-app flow:

1. On startup, check whether the configured Playwright browser path exists.
2. If missing, show a clear setup state in the UI.
3. Ask the user before downloading browser binaries.
4. Download only into the app data directory.
5. Do not use or delete Codex, Claude, Chrome, or system Playwright browser caches.
6. Record browser path and version in diagnostics.

## E. Lifecycle

Startup flow:

1. Check `http://127.0.0.1:8422/api/health`.
2. If healthy, reuse existing backend.
3. If unhealthy, check whether port `8422` is occupied.
4. If occupied but not healthy, report a port conflict and do not start another backend.
5. If port is free, start the sidecar.
6. Pass explicit runtime, settings, and Playwright paths.
7. Poll `/api/health`.
8. Load WebView after health is ready.

Shutdown flow:

1. If Tauri started the sidecar, stop only that sidecar process tree.
2. If Tauri reused an existing backend, leave it running.
3. Do not kill unrelated Python or user processes.
4. Log whether backend was reused or started by the app.

## F. Safety Permissions

Security constraints:

- Do not expose arbitrary shell execution.
- Capability should allow only the app window and the intended sidecar flow.
- Do not allow arbitrary filesystem access.
- Do not read daily Chrome or Safari profiles.
- Do not auto-handle login, CAPTCHA, or human verification.
- Do not silently upload evidence or runtime data.
- Do not bundle user credentials.

Current `capabilities/default.json`:

```json
{
  "permissions": ["core:default"]
}
```

This is appropriately minimal for the current dev shell, but formal sidecar APIs need review before enabling additional permissions.

## G. Do Not Bundle

Do not put these into the app bundle:

- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `.env`
- local DB files
- user credentials
- provider login sessions
- Playwright browser cache unless a later explicit packaging decision is made
- `.build-venv/`
- `venv/`
- `apps/desktop/node_modules/`
- build caches

## H. Formal Packaging Prerequisites

Before DMG/EXE/MSI:

- macOS signing identity strategy
- macOS notarization flow
- Windows code signing strategy
- updater design
- installed runtime migration
- settings UI or settings file model
- Playwright browser provisioning
- crash logs and diagnostic bundle
- sidecar process tree shutdown robustness
- port conflict UI
- first-run setup UX
- versioned migration for runtime data
- clear uninstall behavior that preserves or optionally removes user data

## Current Config Assessment

`apps/desktop/src-tauri/tauri.conf.json`:

- Good for dev.
- Not ready for formal sidecar bundle.
- Missing `bundle.externalBin`.
- `bundle.active=false`.
- `beforeDevCommand` is dev-only.

`apps/desktop/src-tauri/capabilities/default.json`:

- Minimal and acceptable for dev.
- Formal sidecar capabilities still need review once Tauri sidecar APIs are wired.

`apps/desktop/src-tauri/run_dev_backend.sh`:

- Good for dev smoke.
- Supports `LOCAL_AI_BACKEND_MODE=python|binary`.
- Uses project-local runtime paths.
- Not an installed-app lifecycle manager.

## Recommendation

Do not run formal `tauri build` yet.

Next stage should be formal sidecar bundle preparation:

1. Rename/copy prototype sidecar to target-triple naming.
2. Add a formal bundle config branch or profile.
3. Replace dev project-root runtime assumptions with installed app data paths.
4. Decide how Tauri will pass app data paths to sidecar.
5. Verify formal sidecar launch in a non-DMG local bundle build only after explicit confirmation.
