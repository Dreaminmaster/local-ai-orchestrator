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

## Tauri Dev Smoke Attempt

Generated: 2026-06-02T21:23:00+08:00

Requested scope:

- no Rust install
- no global Tauri CLI install
- no live Claude
- no other provider tests
- no PyInstaller
- no DMG/EXE/MSI

Environment versions observed from the current shell:

| Tool | Result |
|---|---|
| `rustc --version` | missing from current shell PATH, `command not found` |
| `cargo --version` | missing from current shell PATH, `command not found` |
| `node --version` | `v25.9.0` |
| `npm --version` | `11.12.1` |

Additional Rust lookup:

- `~/.cargo/bin/rustc`: not found
- `~/.cargo/bin/cargo`: not found
- `/opt/homebrew/bin/rustc`: not found
- `/opt/homebrew/bin/cargo`: not found
- `/usr/local/bin/rustc`: not found
- `/usr/local/bin/cargo`: not found

Desktop npm dependency install:

- Command: `npm install`
- Directory: `apps/desktop`
- Result: PASS
- Installed packages: 2
- Vulnerabilities: 0
- Dependency location: `apps/desktop/node_modules`
- Global Tauri CLI used: no
- Project-local `@tauri-apps/cli` used: yes
- Project-local Tauri CLI version: `tauri-cli 2.11.2`
- Generated `apps/desktop/package-lock.json`: yes
- Recommendation: commit `apps/desktop/package-lock.json` so the project-local Tauri CLI version is reproducible; do not commit `apps/desktop/node_modules`.

Backend before Tauri dev:

- `/api/health`: HTTP 200, `"ok": true`
- Listener: PID `55671`
- Command: `Python`
- Port: `8422`
- Backend was already running, so no duplicate backend was started.

Tauri dev command:

```bash
cd apps/desktop
npm run dev
```

Result: BLOCKED

Reason:

```text
failed to run 'cargo metadata' command to get workspace directory:
failed to run command cargo metadata --no-deps --format-version 1:
No such file or directory (os error 2)
```

Interpretation:

- The project-local Tauri CLI starts correctly.
- The Tauri dev window did not open.
- The WebView did not launch.
- The blocker is that `cargo` is not visible to the current shell.
- No formal package build was attempted.

Backend after Tauri dev attempt:

- Listener remains PID `55671`.
- No duplicate backend process was created.
- Because Tauri dev did not start its own backend or WebView, there was no Tauri-started backend to clean up.
- The pre-existing workspace-dev backend was not killed.

Non-live checks after smoke attempt:

- `python3 scripts/health_check.py`: FAIL with system Python because `httpx` is not installed in system Python.
- Borrowed old success venv with `PYTHONPATH` pointing to workspace-dev:
  - `scripts/health_check.py`: PASS
  - `scripts/beta_validation.py`: PASS, live Claude skipped
- `node --check frontend/app.js`: PASS

Current conclusion:

- Tauri dev smoke is not PASS yet.
- Desktop window did not open.
- Product Web UI remains available in browser/backend mode through `http://127.0.0.1:8422`.
- To run Tauri dev, the next step is to make the already-installed Rust/Cargo visible to the shell, or complete Rust/Cargo installation if it did not actually place `cargo` on disk.
- This is still not a formal installer because there is no sidecar binary, no bundle, no signing, no notarization, and no updater.

## FlyEnv Rust Tauri Dev Smoke

Generated: 2026-06-02T21:48:00+08:00

Rust/Cargo were made visible only for the current commands with:

```bash
export PATH="/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin:$PATH"
```

No shell profile, system environment, or global Tauri CLI installation was changed.

Tool versions:

| Tool | Result |
|---|---|
| `rustc --version` | `rustc 1.96.0 (ac68faa20 2026-05-25)` |
| `cargo --version` | `cargo 1.96.0 (30a34c682 2026-05-25)` |
| `which rustc` | `/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin/rustc` |
| `which cargo` | `/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin/cargo` |
| `node --version` | `v25.9.0` |
| `npm --version` | `11.12.1` |

Dev shell fixes made during smoke:

- `apps/desktop/src-tauri/tauri.conf.json`: changed `beforeDevCommand` from `./run_dev_backend.sh` to `./src-tauri/run_dev_backend.sh`.
- `apps/desktop/src-tauri/run_dev_backend.sh`: made backend reuse more conservative so an occupied port 8422 does not trigger a duplicate backend start.
- `apps/desktop/src-tauri/icons/icon.png`: added a small development icon required by `tauri::generate_context!()`.

Tauri dev run:

```bash
cd apps/desktop
npm run dev
```

Result: PASS.

Observed output:

```text
Finished `dev` profile [unoptimized + debuginfo] target(s)
Running `target/debug/local-ai-orchestrator-desktop`
[desktop] backend already healthy at http://127.0.0.1:8422/api/health
```

Current running dev processes:

- Tauri dev node process: PID `99828`
- Desktop app process: PID `99929`, `target/debug/local-ai-orchestrator-desktop`
- Backend process: PID `55671`

Backend lifecycle:

- Existing backend was reused.
- No duplicate backend remains.
- `/api/health` returned `"ok": true`.
- Backend listener after smoke: only PID `55671` on port `8422`.

Generated development artifacts:

- `apps/desktop/node_modules/`
- `apps/desktop/package-lock.json`
- `apps/desktop/src-tauri/target/`
- Cargo registry/cache artifacts outside the project, created by the Rust dev build.

Commit guidance:

- Commit `apps/desktop/package-lock.json`.
- Commit `apps/desktop/src-tauri/tauri.conf.json`.
- Commit `apps/desktop/src-tauri/run_dev_backend.sh`.
- Commit `apps/desktop/src-tauri/icons/icon.png`.
- Do not commit `apps/desktop/node_modules/`.
- Do not commit `apps/desktop/src-tauri/target/`.
- Do not commit runtime data.

Why this is still not a formal installer:

- This was `tauri dev`, not `tauri build`.
- No Python backend sidecar binary exists.
- No PyInstaller step was run.
- No DMG/EXE/MSI was produced.
- No signing, notarization, updater, or release pipeline was configured.

## Backend Binary Mode Smoke

Generated: 2026-06-02T23:21:00+08:00

Build environment:

- `.build-venv`: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv`
- PyInstaller: `6.20.0`
- Binary: `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`
- Binary size: about `74M`

Tauri backend modes:

- `LOCAL_AI_BACKEND_MODE=python`: Python dev backend mode.
- `LOCAL_AI_BACKEND_MODE=binary`: backend sidecar prototype mode.

Binary mode smoke result: PASS.

Verified:

- Tauri dev started with `LOCAL_AI_BACKEND_MODE=binary`.
- `run_dev_backend.sh` launched the backend binary.
- `/api/health` returned `"ok": true`.
- WebView loaded the product UI.
- No duplicate backend remained.
- Closing Tauri stopped only the binary backend started by the script.
- No backend process remained on `8422` after binary-mode close.

Existing backend reuse result: PASS.

Verified:

- A manual Python backend was started.
- Tauri dev was launched with `LOCAL_AI_BACKEND_MODE=binary`.
- Tauri reused the existing healthy backend.
- It did not start the binary.
- Closing Tauri did not kill the manually started backend.
- The manual test backend was stopped afterward as test cleanup.

Current status:

- Tauri dev shell can run against a Python backend or a prototype binary backend.
- This is still not a formal installer: no `tauri build`, no `bundle.externalBin`, no DMG/EXE/MSI, no signing, no notarization, no updater.

## Formal Sidecar Bundle Assessment

Generated: 2026-06-02T23:35:00+08:00

Formal sidecar bundle plan:

`FORMAL_SIDECAR_BUNDLE_PLAN.md`

Current status:

- Tauri dev shell: PASS.
- Binary backend dev mode: PASS.
- Formal sidecar bundle: not ready.

Why not ready:

- `bundle.active=false`.
- `bundle.externalBin` is absent.
- Prototype binary is named `local-ai-orchestrator-backend`, not target-triple-specific.
- Installed runtime directory is not implemented.
- Playwright browser provisioning is not implemented.
- `beforeDevCommand` is a dev shell mechanism, not a formal installed-app lifecycle manager.

Do not run yet:

- `npm run tauri build`
- `cargo build --release` for release packaging
- `tauri build`
- DMG/EXE/MSI
- signing
- notarization
- updater
