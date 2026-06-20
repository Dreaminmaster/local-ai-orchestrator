# First Run Experience Report

Generated: 2026-06-03

## Result

First run experience and local diagnostics smoke: **PASS**

The product shell now exposes first-launch status, local app data access,
diagnostics export, and conservative cache cleanup without requiring terminal
commands.

## First Run Status Page

The right-side product panel now displays API-driven status for:

- Backend: running / error
- App data path
- Project browser: installed / missing
- Claude workspace state
- ChatGPT workspace state
- LM Studio: connected / disconnected
- Ollama: connected / disconnected
- Current mode: packaged app / browser dev / tauri dev

Packaged mode shows app data paths and does not display workspace-dev as the
runtime root.

## App Data API

Added:

- `GET /api/app-data/status`
- `POST /api/app-data/open`
- `POST /api/app-data/clear-cache`
- `POST /api/diagnostics/export`

Packaged smoke result:

- app data exists: true
- app data writable: true
- open app data directory: PASS
- settings path: app data root
- runtime, logs, browser profiles, evidence, reports, and Playwright paths:
  app data

The open API is restricted to the resolved app data directory and does not
accept an arbitrary path.

## Diagnostics Export

Diagnostic package generated:

```text
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/
diagnostics/local-ai-orchestrator-diagnostics-20260603-115920.zip
```

Included:

- `health.json`
- `settings.redacted.json`
- `provider_status.json`
- `playwright_status.json`
- `app_data_status.json`
- desktop and sidecar logs

Confirmed excluded:

- `.env`
- API keys and secrets
- browser profiles
- cookies
- provider conversation content
- evidence files
- uploaded files
- runtime database

## Safe Cache Cleanup

The cache cleanup endpoint removes only:

- runtime temp files
- test reports
- pip cache
- old logs beyond the retained recent set

Smoke sentinels confirmed removal of temp, test report, and pip cache files.

Confirmed preserved:

- `settings.json`
- browser profiles
- evidence
- tasks
- user files
- Claude and ChatGPT login profiles

Provider profile reset now requires an explicit confirmation request before
deleting the selected project-owned profile.

## Playwright Browser Missing UX

The packaged app reported:

- configured path: app data Playwright browser directory
- Chromium found: false
- auto download: false

The UI displays:

```text
项目专用浏览器未安装。外部 AI 网页控制可能不可用。
```

Available actions:

- 查看安装说明
- 暂不安装

No browser download was attempted.

## Packaged App Smoke

- packaged app launch: PASS
- bundled onedir sidecar: PASS
- `/api/health`: PASS
- `/api/ui-ready`: PASS
- frontend loaded: true
- health panel rendered: true
- app data open: PASS
- diagnostics export: PASS
- cache cleanup: PASS
- sidecar shutdown: PASS
- final port `8422` residue: none

An additional Playwright screenshot check was not run because the project
browser executable is missing. No browser was downloaded.

## Offline Validation

- app data and diagnostics unit tests: PASS
- runtime paths, settings, and Playwright status tests: PASS
- total focused tests: 10 PASS
- `node --check frontend/app.js`: PASS
- `scripts/health_check.py`: PASS
- `scripts/beta_validation.py`: PASS, live Claude skipped
- Rust `cargo check`: PASS

## Conclusion

The app can enter the **user-testable unsigned DMG** stage.

It remains unsigned, not notarized, and not a formal public release.
