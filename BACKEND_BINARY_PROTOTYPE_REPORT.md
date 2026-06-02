# Backend Binary Prototype Report

Generated: 2026-06-02T23:04:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: Python backend sidecar binary prototype only. No live Claude, no provider tests, no browser profile reset, no PyInstaller install, no generated binary, no Tauri formal bundle, no DMG/EXE/MSI, no signing, no notarization, and no updater work was performed.

## Backend Entry Analysis

Current entries:

- `run.py`: convenience launcher that imports `backend.main.main`.
- `backend.main`: FastAPI app definition and existing CLI entry.
- `backend.main.app`: FastAPI application object.
- `backend.main.main()`: loads `.env`, reads `HOST` / `PORT`, and runs `uvicorn.run(app, host=..., port=...)`.
- `/api/health`: mounted through `backend.api.health.router` under `/api`.

Current backend runtime assumptions:

- `backend.main` inserts the project root into `sys.path`.
- `.env` is loaded at process startup by `backend.main.main()`.
- Runtime paths are mostly project-relative, such as `runtime/tasks`, `runtime/evidence`, and `runtime/test_reports`.
- `PLAYWRIGHT_BROWSERS_PATH` is read from the environment, defaulting to project-local `.playwright-browsers`.

Conclusion:

- Best PyInstaller prototype entry: `backend.sidecar_entry`.
- Reason: `run.py` and `backend.main.main()` are useful for dev, but a sidecar binary needs explicit control over `--host`, `--port`, `--project-root`, `--runtime-dir`, `--playwright-browsers-path`, `--version`, and `--health-check-only`.

## Added Sidecar CLI Entry

Added:

`backend/sidecar_entry.py`

Supported arguments:

- `--host`
- `--port`
- `--project-root`
- `--runtime-dir`
- `--playwright-browsers-path`
- `--version`
- `--health-check-only`

Behavior:

- Default host: `127.0.0.1`.
- Default port: `8422`.
- Sets `PROJECT_ROOT`.
- Sets `PYTHONPATH`.
- Sets `PLAYWRIGHT_BROWSERS_PATH`.
- Creates runtime directories when missing.
- Does not embed `.env`.
- Does not embed runtime, profiles, evidence, or test reports.

Source-level validation:

```text
local-ai-orchestrator-backend 0.2.1-tauri-dev-pass
```

`--health-check-only` result:

```json
{
  "ok": true,
  "version": "0.2.1-tauri-dev-pass",
  "project_root": "/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev",
  "runtime_dir": "/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime",
  "playwright_browsers_path": "/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.playwright-browsers",
  "env_file_embedded": false,
  "runtime_embedded": false
}
```

## Added Build Script

Added:

`scripts/build_backend_binary.py`

Behavior:

- Uses the current Python executable.
- Checks whether PyInstaller is available.
- Does not install PyInstaller.
- Outputs prototype binary to `apps/desktop/src-tauri/bin/`.
- Intended binary name: `local-ai-orchestrator-backend`.
- Uses build cache under `build/backend_binary/`.

Build command attempted:

```bash
/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python scripts/build_backend_binary.py
```

Result:

```text
PyInstaller missing
Python: /Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python
Install PyInstaller into the project venv or approved build venv first.
Suggested after confirmation: venv/bin/pip install pyinstaller
No install was attempted.
```

## PyInstaller Status

- System Python: PyInstaller missing.
- Old success venv: PyInstaller missing.
- No PyInstaller install was attempted.

Suggested install after user confirmation:

```bash
/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/pip install pyinstaller
```

Preferred for cleaner prototype:

```bash
cd /Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/pip install pyinstaller
```

This would be a venv development dependency, not a global install. It should not be committed, and `venv/` should remain excluded.

## Binary Result

- Binary generated: no.
- Expected binary path: `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`.
- Binary size: not available.
- Binary `--version`: not run, because binary does not exist.
- Binary `--health-check-only`: not run, because binary does not exist.
- Binary `/api/health`: not run, because binary does not exist.

## Tauri Dev Binary Mode

Updated:

`apps/desktop/src-tauri/run_dev_backend.sh`

New mode:

```bash
LOCAL_AI_BACKEND_MODE=binary
```

Mode behavior:

- Always checks `/api/health` first.
- If healthy, reuses the existing backend.
- If not healthy and port `8422` is occupied, does not start a duplicate backend.
- If mode is `binary`, starts `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`.
- If the binary is missing, prints a clear message and exits.
- If mode is `python`, keeps the current Python dev backend behavior.
- On shutdown, stops only the backend process started by this script.

Tauri dev binary mode verification:

- Not run with a binary, because PyInstaller is missing and no binary exists.
- Existing backend reuse remains verified from prior Tauri dev smoke.

## Current `/api/health`

Current running backend:

- PID: `55671`
- Command: Python `-m backend.main`
- Port: `8422`

Health response:

```json
{
  "ok": true,
  "backend": "running",
  "portable_mode": true
}
```

Duplicate backend:

- No duplicate backend remains.
- No `local-ai-orchestrator-backend` process exists.

## Non-Live Checks

Literal system Python:

- `python3 scripts/health_check.py`: FAIL, system Python lacks `httpx`.
- `python3 scripts/beta_validation.py`: FAIL for the same dependency reason.

Borrowed old success venv with `PYTHONPATH` pointing to workspace-dev:

- `scripts/health_check.py`: PASS.
- `scripts/beta_validation.py`: PASS, live Claude skipped.
- `node --check frontend/app.js`: PASS.

## Why This Is Still Not A Formal Installer

- No backend binary exists yet.
- No Tauri `externalBin` is configured.
- No `tauri build` was run.
- No PyInstaller artifact was produced.
- No DMG/EXE/MSI was produced.
- No signing, notarization, updater, or release pipeline exists.
- Playwright browsers are not bundled.
- Python is not automatically installed.
- Runtime data remains external and user-writable.

## Next Step For Prototype

Ask for confirmation to install PyInstaller into an approved venv.

After confirmation:

1. Install PyInstaller into the selected venv only.
2. Run `scripts/build_backend_binary.py`.
3. Verify `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend --version`.
4. Verify `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend --health-check-only`.
5. Stop the current Python backend only if it was started for this test and user confirms.
6. Start the backend binary on `127.0.0.1:8422`.
7. Verify `curl http://127.0.0.1:8422/api/health`.
8. Run Tauri dev with `LOCAL_AI_BACKEND_MODE=binary`.
9. Verify WebView loads the UI.
10. Close Tauri and confirm only the binary sidecar exits.

Do not enter formal sidecar bundle or installer design until the prototype binary lifecycle passes.

## Prototype Build Follow-Up

Generated: 2026-06-02T23:21:00+08:00

Build environment:

- `.build-venv` path: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv`
- Python: `.build-venv/bin/python`
- PyInstaller: `6.20.0`
- Install scope: workspace-dev `.build-venv` only
- Global PyInstaller install: no
- System Python modified: no
- Old success venv modified: no

Note: pip used the default user wheel cache under `~/Library/Caches/pip` while building wheels. This was cache usage, not a global package installation.

Build command:

```bash
.build-venv/bin/python scripts/build_backend_binary.py --clean
```

Build result: PASS.

Binary:

- Generated: yes
- Path: `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`
- Size: `77,553,472` bytes, about `74M`
- Type: Mach-O 64-bit executable arm64

Binary basic checks:

```text
local-ai-orchestrator-backend 0.2.1-tauri-dev-pass
```

`--health-check-only` result: PASS.

```json
{
  "ok": true,
  "version": "0.2.1-tauri-dev-pass",
  "env_file_embedded": false,
  "runtime_embedded": false
}
```

Direct binary backend test:

- Started binary with `--host 127.0.0.1 --port 8422`.
- `/api/health`: PASS, returned `"ok": true`.
- Listening process: PyInstaller onefile child process.
- Duplicate backend: no.

Tauri dev binary mode:

- Command mode: `LOCAL_AI_BACKEND_MODE=binary`.
- Tauri dev shell: PASS.
- Backend startup: binary was started by `run_dev_backend.sh`.
- `/api/health`: PASS.
- WebView/product UI: loaded through Tauri dev.
- Duplicate backend: no.
- Close behavior: PASS. Closing the Tauri dev process group stopped only the binary backend it started.
- Residual backend after binary mode close: none.

Existing backend reuse scenario:

- Manually started Python backend PID `23325`.
- Started Tauri dev with `LOCAL_AI_BACKEND_MODE=binary`.
- Tauri beforeDevCommand detected backend already healthy.
- No binary backend was started.
- After closing Tauri dev, Python backend PID `23325` remained running, as intended.
- The manually started test backend was then stopped by this test cleanup.

Non-live checks:

- `.build-venv/bin/python scripts/health_check.py`: PASS.
- `.build-venv/bin/python scripts/beta_validation.py`: PASS, live Claude skipped.
- `node --check frontend/app.js`: PASS.

Ignored prototype artifacts:

- `.build-venv/`
- `build/`
- `dist/`
- `*.spec`
- `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`
- `apps/desktop/src-tauri/target/`

Current conclusion:

- Backend binary prototype lifecycle is PASS.
- The project can enter formal sidecar bundle design.
- It is still not a formal installer because no Tauri bundle, DMG/EXE/MSI, signing, notarization, updater, Playwright browser packaging, or production runtime location design has been completed.

## Formal Sidecar Bundle Design Follow-Up

Generated: 2026-06-02T23:35:00+08:00

Formal sidecar bundle plan:

`FORMAL_SIDECAR_BUNDLE_PLAN.md`

Current Tauri config assessment:

- `tauri.conf.json` is still dev-only.
- `bundle.active=false`.
- `bundle.externalBin` is not configured.
- `beforeDevCommand` is dev-only.
- `run_dev_backend.sh` supports binary mode but still assumes project-local dev paths.
- `capabilities/default.json` is minimal with `core:default`, which is good for dev, but formal sidecar permissions still need review before adding process/shell capabilities.

Formal bundle readiness:

- Prototype backend binary: ready.
- Formal externalBin naming: not implemented.
- Installed runtime path model: designed, not implemented.
- Playwright browser provisioning: designed, not implemented.
- Formal Tauri build: intentionally not run.
