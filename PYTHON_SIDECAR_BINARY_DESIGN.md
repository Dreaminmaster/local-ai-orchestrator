# Python Sidecar Binary Design

Generated: 2026-06-02T22:05:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: design only. No PyInstaller run, no backend binary generation, no Tauri build, no DMG/EXE/MSI, no signing, no notarization, and no updater work has been performed.

## 1. Current State

- Tauri dev shell can open the local product UI.
- Tauri dev uses the project-local `@tauri-apps/cli`, not a global Tauri CLI.
- FlyEnv Rust/Cargo is available when the command PATH includes `/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin`.
- Current backend still depends on Python and a venv.
- Current Tauri dev shell reuses an existing healthy backend on `http://127.0.0.1:8422`.
- `/api/health` returns `"ok": true`.
- This is not a formal installer. It is a development shell.

## 2. Sidecar Binary Goal

The sidecar goal is to make the Python backend available as a local executable that Tauri can launch and manage.

Target behavior:

- Tauri starts the backend sidecar when no healthy backend is already running.
- Backend sidecar serves `GET /api/health`.
- Tauri WebView loads `http://127.0.0.1:8422`.
- If a healthy backend already exists, Tauri does not start a duplicate backend.
- When the app closes, Tauri stops only the sidecar process it started itself.
- Tauri must not kill unrelated Python, backend, LM Studio, Codex, Chrome, Safari, or user processes.

## 3. Packaging Candidates

### PyInstaller

Pros:

- Mature and widely used for Python application binaries.
- Good first prototype path for FastAPI/uvicorn style apps.
- Supports collecting Python modules, package data, and hidden imports.
- Easy to test incrementally before formal desktop packaging.

Cons:

- Hidden imports may need careful tuning.
- Binary size can be large.
- Playwright browser binaries and user runtime data must remain external.
- macOS signing/notarization is a later separate concern.

### Nuitka

Pros:

- Can produce optimized compiled binaries.
- Often gives stronger packaging behavior for larger apps.

Cons:

- More moving parts for a first prototype.
- Build time can be longer.
- Dependency and plugin tuning may take more work than PyInstaller.

### Briefcase

Pros:

- App-oriented Python packaging model.
- Can be useful for platform-native app distribution.

Cons:

- Less direct fit for a Tauri sidecar-first architecture.
- Better treated as research, not the first prototype.

### PyOxidizer

Pros:

- Strong embedding model.
- Can produce compact self-contained executables in some scenarios.

Cons:

- Higher integration complexity.
- More friction with dynamic Python packages and browser automation dependencies.
- Not recommended for the first prototype.

## 4. Recommended Prototype Path

Use PyInstaller first, only as a prototype.

Do not immediately enter formal installer packaging.

Prototype goals:

- Verify the backend binary starts.
- Verify FastAPI routes load.
- Verify `/api/health` works.
- Verify backend modules import correctly.
- Verify runtime read/write paths still point outside the binary.
- Verify Playwright browser/profile paths remain configurable.
- Verify the binary can be started by Tauri dev.
- Verify shutdown only stops the sidecar process Tauri started.

## 5. Path Design

The backend binary should contain only executable program code and required packaged Python dependencies.

Do not bake these into the binary:

- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `.env`
- `.playwright-browsers/`
- user login sessions
- provider evidence
- local task data

Runtime path model:

- In dev, runtime can remain under the project directory.
- In a future installed app, runtime should live in a user-writable app data directory.
- `PLAYWRIGHT_BROWSERS_PATH` must remain configurable.
- Browser profiles must remain under a controlled project/app runtime path, not daily Chrome/Safari profiles.
- `.env` remains an external configuration file or app-managed settings source; it is not embedded into the binary.

## 6. Lifecycle Design

Tauri startup flow:

1. Check `http://127.0.0.1:8422/api/health`.
2. If healthy, reuse that backend and mark it as externally existing.
3. If not healthy, check whether port `8422` is occupied.
4. If port is occupied but not healthy, do not start a duplicate backend. Report the conflict.
5. If no healthy backend and port is free, start the sidecar binary.
6. Save the sidecar PID.
7. Poll `/api/health` until ready or timeout.
8. Load WebView at `http://127.0.0.1:8422`.

Tauri shutdown flow:

1. If Tauri started a sidecar PID, stop only that PID.
2. If Tauri reused an existing backend, do not kill it.
3. Never kill unrelated Python processes.
4. Never kill other tools or browsers.
5. Log shutdown result for diagnostics.

## 7. Safety Boundaries

- Do not expose arbitrary shell execution from Tauri.
- Tauri capabilities should permit only the project sidecar flow.
- Do not add broad filesystem permissions.
- Do not automatically handle Claude login, CAPTCHA, or human verification.
- Do not read daily Chrome/Safari profiles.
- Do not submit user runtime data to Git.
- Do not package browser profiles, evidence, local reports, or `.env`.
- Do not silently fall back to untested providers.

## 8. Verification Plan

Backend binary checks:

```bash
backend-sidecar --version
backend-sidecar --health
```

Backend serving checks:

```bash
backend-sidecar
curl http://127.0.0.1:8422/api/health
```

Lifecycle checks:

- Start Tauri dev with no backend running.
- Confirm Tauri starts sidecar binary.
- Confirm `/api/health` returns `"ok": true`.
- Confirm WebView shows the product UI.
- Close Tauri.
- Confirm the sidecar PID exits.
- Confirm no unrelated Python/backend process was killed.

Reuse checks:

- Start backend manually.
- Start Tauri dev.
- Confirm Tauri reuses existing backend.
- Close Tauri.
- Confirm manually started backend remains running.

Conflict checks:

- Occupy port `8422` with a non-health server.
- Start Tauri dev.
- Confirm Tauri does not start a duplicate sidecar.
- Confirm UI reports a clear port conflict or backend unhealthy state.

## 9. Temporarily Out Of Scope

Do not do these in the sidecar design phase:

- DMG
- EXE
- MSI
- signing
- notarization
- updater
- automatic Python installation
- automatic Playwright browser packaging
- production installer UX
- automatic Claude login
- daily Chrome/Safari profile access

## Next Step

After user confirmation, enter backend binary prototype phase:

1. Draft a PyInstaller spec or command.
2. Build a local prototype binary.
3. Verify backend imports and `/api/health`.
4. Wire Tauri dev to the prototype sidecar.
5. Verify lifecycle behavior.

Only after that should formal installer packaging be considered.
