# Tauri Dev Shell Report

Generated: 2026-06-02T17:05:30+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

## Environment Check

| Tool | Result |
|---|---|
| Node | `v25.9.0` |
| npm | `11.12.1` |
| rustc | missing |
| cargo | missing |
| Tauri CLI | missing |

No global install was attempted.

Tauri dev shell is **not runnable locally yet** because Rust/Cargo/Tauri CLI are missing.

## Existing Desktop Structure

Present:

- `apps/desktop/package.json`
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/src-tauri/tauri.conf.json`
- `apps/desktop/src-tauri/src/main.rs`

Added:

- `apps/desktop/src-tauri/capabilities/default.json`
- `apps/desktop/src-tauri/run_dev_backend.sh`
- `apps/desktop/run_dev.sh`
- `apps/desktop/run_dev_windows.ps1`
- `apps/desktop/README.md`

## Tauri Config

- `devUrl`: `http://127.0.0.1:8422`
- main window title: `Local AI Orchestrator`
- window size: `1440x1000`
- `bundle.active`: `false`
- no DMG/EXE/MSI bundle config
- no `externalBin`
- no PyInstaller sidecar binary

This is a dev shell only.

## Backend Launch Strategy

Dev launcher:

`apps/desktop/src-tauri/run_dev_backend.sh`

Behavior:

1. Checks `http://127.0.0.1:8422/api/health`.
2. If healthy, does not start a second backend.
3. If not healthy, starts backend from the project root.
4. Sets portable env:
   - `PROJECT_ROOT`
   - `PYTHONPATH`
   - `PLAYWRIGHT_BROWSERS_PATH`
   - `PIP_CACHE_DIR`
   - `TMPDIR`
5. Python priority:
   - workspace-dev `venv/bin/python`
   - old success venv `/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python`
6. On exit, stops only the backend process it started itself.

No dependencies are installed by the launcher.

## Health API

Added:

`GET /api/health`

Expected response includes:

- `ok`
- `backend`
- `portable_mode`
- `project_root`
- `runtime_dir`
- `playwright_browsers_path`
- `lmstudio_reachable`
- `external_ai.claude`
- `external_ai.chatgpt`

Code-level health validation passed by directly calling the handler.

Current HTTP check:

- Previous backend on port 8422 was PID `50920`, cwd `/Users/johnwick/Documents/codex/local-ai-orchestrator-main`.
- That process was identified as the old local project backend and stopped.
- Workspace-dev backend is now running as PID `55671`, cwd `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`.
- `http://127.0.0.1:8422/api/health` returned HTTP OK with `"ok": true`.
- Response project root: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`.
- Portable mode: `true`.
- Runtime dir: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime`.
- Playwright browsers path: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.playwright-browsers`.
- LM Studio status from health endpoint: `false` in this run.
- External AI status from health endpoint: Claude `READY`, ChatGPT `NOT_CONFIGURED`.

## Frontend Desktop Status

Top system status now reads `/api/health` and displays:

- Backend
- Portable mode
- LM Studio
- External AI
- Desktop Shell
- Current task

Desktop shell mode:

- Tauri WebView: `dev`
- ordinary browser: `browser mode`

Verified browser-mode frontend status:

- Backend: `running`
- Portable mode: `OK`
- LM Studio: `disconnected`
- External AI: `Claude READY / ChatGPT NOT_CONFIGURED`
- Desktop Shell: `browser mode`
- Current task: `external_ai_manual`
- Screenshot saved under runtime test reports: `runtime/test_reports/web_product_shell_health.png`

## Tauri Dev Smoke

`apps/desktop/run_dev.sh` was executed.

Result:

- environment check worked
- no install attempted
- exited safely because `cargo`, `rustc`, and Tauri CLI are missing
- Tauri WebView was not launched
- no backend was started by the script
- no extra backend process was created

## Non-Live Checks

- `scripts/health_check.py`: PASS
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10
- `node --check frontend/app.js`: PASS
- workspace recovery unittest: PASS
- workspace login state unittest: PASS
- answer quality unittest: PASS
- beta validation status unittest: PASS
- pending External AI resume tests: PASS
- `scripts/beta_validation.py`: PASS, live Claude skipped

Latest requested verification:

- port 8422 listener: workspace-dev backend PID `55671`
- `/api/health`: PASS, `"ok": true`
- frontend top system status reads `/api/health`: PASS
- `scripts/health_check.py`: PASS
- `scripts/beta_validation.py`: PASS, live Claude skipped
- `node --check frontend/app.js`: PASS

## Runtime Data Exclusion

Do not commit:

- `runtime/`
- `venv/`
- `.playwright-browsers/`
- `.env`
- browser profiles
- evidence
- test reports
- `target/`
- `node_modules/`
- `apps/desktop/node_modules/`
- `apps/desktop/src-tauri/target/`

`.gitignore` was updated for Node/Tauri build outputs.

## Why This Is Not A Formal Installer

- Rust/Cargo/Tauri CLI are not installed locally.
- No Python backend sidecar binary exists.
- No PyInstaller step has been created.
- No `bundle.externalBin` has been configured.
- `bundle.active=false`.
- No DMG/EXE/MSI is built.
- No signing, notarization, updater, or release pipeline exists.

## Next Steps For Real Sidecar Binary

1. Ask for explicit confirmation before installing Rust/Cargo and Tauri CLI in a controlled dev environment.
2. Create a workspace-local Node dependency install for `apps/desktop`.
3. Validate `tauri dev` opens the WebView and does not duplicate backend processes.
4. Build a Python backend binary with PyInstaller or equivalent.
5. Add Tauri `bundle.externalBin` with the target-triple sidecar name.
6. Restrict shell/sidecar permissions in capabilities.
7. Only then prepare DMG/EXE/MSI packaging.
