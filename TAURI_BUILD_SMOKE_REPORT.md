# Tauri Build Smoke Report

Generated: 2026-06-03T01:50:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: controlled local Tauri build smoke. No live Claude, no other provider tests, no profile reset, no formal DMG/EXE/MSI release, no signing, no notarization, and no updater work was performed.

## Environment Signals

Commands checked:

- `rustc -vV` through FlyEnv Rust
- `cargo -vV` through FlyEnv Rust
- `uname -m`
- `arch`
- `node -p "process.arch"`

Results:

- FlyEnv `rustc` host: `x86_64-apple-darwin`
- FlyEnv `cargo` host: `x86_64-apple-darwin`
- `uname -m`: `arm64`
- `arch`: `arm64`
- Node arch: `arm64`
- PyInstaller backend binary: `Mach-O 64-bit executable arm64`

Why the previous smoke generated the wrong sidecar name:

- The old prepare script trusted `rustc -vV` host only.
- FlyEnv Rust reports `x86_64-apple-darwin`.
- Tauri bundler and the generated backend binary are arm64 on this machine.
- Tauri therefore required `local-ai-orchestrator-backend-aarch64-apple-darwin`.

## Fixes Applied

### Sidecar Target Naming

Updated:

`scripts/prepare_tauri_sidecar_binary.py`

New behavior:

- supports `--target aarch64-apple-darwin`
- supports `--target x86_64-apple-darwin`
- supports `--auto`
- supports `--all-macos`
- if no target can be selected, prints explicit target options instead of guessing
- explicit `--target` still works when `rustc` is not on PATH

For this smoke, generated:

`apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-aarch64-apple-darwin`

This generated binary is local output and must not be committed.

### Tauri Sidecar Lifecycle

Updated:

`apps/desktop/src-tauri/src/main.rs`

Implemented:

- startup health check for `http://127.0.0.1:8422/api/health`
- reuse existing healthy backend
- start bundled sidecar if no healthy backend exists
- use app data runtime:
  `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime`
- use app data Playwright path:
  `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/playwright-browsers`
- write sidecar output to:
  `runtime/logs/desktop-sidecar.log`
- stop only the child process started by the app on normal Tauri exit

Permissions:

- no shell plugin was added
- no broad filesystem permissions were added
- `capabilities/default.json` remains `core:default`

### Packaged Frontend API Base

Updated:

`frontend/app.js`

When running under Tauri, frontend requests now target:

`http://localhost:8422`

instead of the Tauri asset origin.

## Build Commands

Backend binary:

```bash
.build-venv/bin/python scripts/build_backend_binary.py
```

Target sidecar:

```bash
.build-venv/bin/python scripts/prepare_tauri_sidecar_binary.py --target aarch64-apple-darwin
```

Tauri build:

```bash
cd apps/desktop
PATH="/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin:$PATH" npm run build
```

Note:

`npm run tauri build` is not a valid script in this package. The actual script is `npm run build`, which runs `tauri build`.

## Build Result

Status: **BUILD PASS / RUNTIME PARTIAL**

Tauri generated:

- `apps/desktop/src-tauri/target/release/local-ai-orchestrator-desktop`
- `apps/desktop/src-tauri/target/release/bundle/macos/Local AI Orchestrator.app`

Bundled app contains:

- `Contents/MacOS/local-ai-orchestrator-desktop`
- `Contents/MacOS/local-ai-orchestrator-backend`

No DMG/EXE/MSI, signing, notarization, or updater was performed.

## Runtime Smoke Result

`.app` opened and launched:

- desktop process
- PyInstaller sidecar parent process
- PyInstaller sidecar child server process

Sidecar log showed:

```text
Started server process
Application startup complete.
Uvicorn running on http://127.0.0.1:8422
GET /api/health HTTP/1.1" 200 OK
```

Observed `/api/health` payload from the packaged sidecar during smoke:

```json
{
  "ok": true,
  "backend": "running",
  "portable_mode": false,
  "runtime_mode": "custom"
}
```

However, external `curl` validation became unreliable in this smoke:

- `lsof` confirmed the sidecar was listening on `127.0.0.1:8422`.
- sidecar logs showed repeated `GET /api/health` `200 OK`.
- some external `curl --max-time` calls hung instead of returning promptly.

Because of that, WebView health display could not be conclusively marked PASS in this run.

## Packaged Runtime Smoke Follow-up

The runtime smoke was tightened with:

- fast cached LM Studio status inside `/api/health`
- Python `http.client` probes with a hard 3-second timeout
- `GET /api/ui-ready`
- frontend `data-app-ready="true"` and `window.LOCAL_AI_UI_READY=true`
- frontend POST `/api/ui-ready` after the health panel renders
- Rust lifecycle log: `desktop-main.log`
- sidecar log: `desktop-sidecar.log`
- graceful `SIGTERM`, 5-second wait, then kill fallback for only the app-started child PID
- `scripts/tauri_packaged_runtime_smoke.py`

### Curl Hang Diagnosis

The original `/api/health` route synchronously checked both LM Studio URLs on every request, with up to 1.5 seconds per URL. Repeated packaged health probes could queue behind those blocking checks, so the server eventually logged `200 OK` after client timeouts.

The route now:

- caches LM Studio reachability for 10 seconds
- uses a 0.25-second endpoint timeout
- keeps the readiness response fast

The smoke no longer relies on an unbounded curl loop.

### Latest Controlled Smoke

Command:

```bash
.build-venv/bin/python scripts/tauri_packaged_runtime_smoke.py --startup-timeout 240
```

Latest result: **FAIL at `sidecar_health_ready` timeout**.

Observed:

- `.app` desktop process started.
- App spawned bundled sidecar PID `75102`.
- Sidecar did not listen on `127.0.0.1:8422` within 180 seconds.
- `desktop-sidecar.log` remained empty.
- `/api/health` could not be reached.
- `/api/ui-ready` could not be reached.
- WebView readiness marker could not be confirmed.
- Normal app quit was requested.
- App-started sidecar PID `75102` exited gracefully.
- Final `8422` listener: none.
- Final packaged app processes: none.

Main lifecycle log:

```text
app_start packaged_tauri=true
backend_health_check_start http://127.0.0.1:8422/api/health
backend_health_check_result ok=false reused_existing=false
sidecar_spawn_start
sidecar_spawn_pid pid=75102
backend_health_check_result ok=false timeout=true
sidecar_health_ready ok=false
app_close normal_exit=true
sidecar_shutdown_start pid=75102
sidecar_shutdown_done pid=75102 graceful=true
```

This shows the remaining blocker is the bundled PyInstaller onefile sidecar cold-start/boot stage, before Uvicorn writes any log or opens the port.

## Shutdown Result

After the last smoke run, the local smoke processes were manually cleaned:

- desktop process stopped
- sidecar parent/child stopped
- final `8422` listener check: no listener

Normal app-quit cleanup: PASS in the latest controlled smoke.

## Current Blockers

Build blocker fixed:

- `aarch64-apple-darwin` sidecar naming now works.
- Tauri `.app` bundling now completes.

Runtime blockers remaining:

- Bundled PyInstaller onefile sidecar can fail to reach Uvicorn within 180 seconds.
- WebView readiness cannot pass until sidecar health is ready.
- The packaged sidecar boot strategy likely needs a focused onefile-versus-onedir prototype decision.

Likely next focused fix:

- investigate the bundled PyInstaller onefile boot stage
- consider an onedir sidecar prototype or a smaller binary build
- rerun one final runtime smoke only after that decision

## Do Not Commit

Do not commit:

- `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`
- `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-aarch64-apple-darwin`
- `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-x86_64-apple-darwin`
- `apps/desktop/src-tauri/target/`
- generated `.app`
- `.build-venv/`
- `runtime/`
- `.env`
- `.playwright-browsers/`
- local app-data runtime

## Recommendation

Do not sync/tag yet.

The code has reached **Tauri build PASS** and **sidecar lifecycle cleanup PASS**, but packaged sidecar startup remains unreliable. Runtime smoke is still **PARTIAL**, so this is not ready for a stable alpha tag.

Next-stage decision:

- Do not enter a broader unsigned macOS app prototype phase yet.
- First resolve the packaged PyInstaller onefile sidecar boot reliability, then rerun one runtime smoke.

## Onedir Packaged Startup Diagnostic

Generated: 2026-06-03

### Scope

This diagnostic replaced the opaque packaged onefile startup path with an
`onedir` prototype. It did not produce a release installer, signing,
notarization, updater, or provider live test.

### Build Strategy

- PyInstaller onefile remains the default build mode.
- `scripts/build_backend_binary.py --mode onedir` now creates:
  `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-dir/`
- The executable is:
  `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend-dir/local-ai-orchestrator-backend`
- Onedir size: approximately `206M`.
- Onedir executable size: `10,654,160` bytes.
- The onedir directory is ignored and must not be committed.
- For this smoke, Tauri `externalBin` remained only as a build-time placeholder.
  The packaged Rust process intentionally preferred the workspace-known onedir
  executable because copying only the executable would separate it from its
  required onedir dependencies.

### Earliest Startup Logging

The Rust launcher now records:

- `sidecar_spawn_command`
- `sidecar_args`
- `sidecar_env`
- `sidecar_working_dir`
- `sidecar_spawn_pid`
- `sidecar_stdout_path`
- `sidecar_stderr_path`

App data log paths:

- `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime/logs/desktop-main.log`
- `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime/logs/desktop-sidecar-stdout.log`
- `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime/logs/desktop-sidecar-stderr.log`

The Python entry also writes `python_entry_reached` and `main_start` to stderr
with flushing enabled.

### Onedir Direct Run

- `--version`: PASS.
- `--health-check-only`: PASS.
- Direct backend startup: PASS.
- `curl --max-time 3 http://127.0.0.1:8422/api/health`: PASS.
- Direct test backend was stopped by its recorded PID.
- Final `8422` listener after direct test: none.

### Controlled Packaged Runtime Smoke

- Tauri build: PASS.
- `.app` generated: PASS.
- Selected sidecar strategy: `onedir_dev_known_path`.
- Sidecar PID: `85666`.
- Python entry log visible: PASS.
- Uvicorn startup visible: PASS.
- Sidecar health ready: PASS, approximately 14 seconds after spawn.
- `127.0.0.1:8422/api/health`: PASS.
- `localhost:8422/api/health`: PASS.
- Sidecar graceful shutdown: PASS.
- Final `8422` listener: none.
- Residual packaged processes: none.

The overall smoke result remains **PARTIAL**, not PASS, because:

- The controlled smoke script returned `final_status=FAIL`.
- `/api/ui-ready` remained at its default state.
- No frontend POST to `/api/ui-ready` appeared in the sidecar log.
- The desktop process exited before UI readiness was confirmed.
- The likely remaining issue is WebView load/navigation timing after the
  synchronous sidecar startup wait in Tauri `.setup()`, not backend startup.

### Conclusion

The previous onefile failure is most consistent with an opaque or unreliable
PyInstaller onefile boot/extraction stage inside the packaged app. Onedir
removed that black box and proved that the packaged Rust launcher can start the
backend, reach Uvicorn, serve health, and clean up its own child.

Recommendation for v0.2.x:

- Prefer an onedir backend sidecar prototype.
- Do not treat onefile as the current packaged sidecar default.
- Resolve WebView readiness/navigation timing before entering the unsigned
  macOS app prototype stage.
- Do not sync or tag this state yet.

## WebView Readiness Final Pass

Generated: 2026-06-03

### Root Cause

The packaged app already included the frontend through Tauri `frontendDist`.
After sidecar health became ready, the Rust launcher navigated the WebView to
`http://127.0.0.1:8422`. The frozen backend does not package the frontend
files, so `/`, `/app.js`, and `/style.css` returned `404`. This prevented the
frontend readiness POST and made UI readiness appear unstable.

### Fix

- The packaged WebView now keeps the Tauri bundled frontend.
- Localhost is used only as the backend API endpoint.
- Rust logs `webview_created` and `webview_load_start`.
- The smoke script validates core runtime independently from UI auto-readiness.
- If UI auto-readiness is unavailable in a future environment, the accepted
  fallback status is `PASS_WITH_MANUAL_UI_CHECK`.

### Controlled Smoke Result

- Tauri build: PASS.
- Onedir sidecar runtime: PASS.
- `127.0.0.1:8422/api/health`: PASS.
- `localhost:8422/api/health`: PASS.
- Frontend source assets present: PASS.
- `webview_created`: true.
- `webview_load_started`: true.
- `/api/ui-ready`: PASS.
- `frontend_loaded`: true.
- `health_panel_rendered`: true.
- `desktop_shell_mode`: `packaged / tauri`.
- Sidecar shutdown: PASS.
- Final `8422` listener: none.
- Residual packaged processes: none.
- Final status: **PASS**.

### Prototype Readiness

The project now meets the runtime conditions for an unsigned macOS app
prototype:

- `.app` builds
- bundled frontend loads
- onedir backend sidecar starts
- backend health is available
- UI health status renders
- app-owned sidecar exits on quit
- no port residue remains

This is still not a release installer. DMG, signing, notarization, updater,
formal onedir resource layout, and production distribution remain separate
work.

## Unsigned DMG Smoke Follow-Up

Generated: 2026-06-03

An unsigned DMG was created with macOS `hdiutil`, mounted, and copied into a
temporary Applications test directory.

Result: **PASS**

- copied app launch: PASS
- packaged sidecar: PASS
- backend health: PASS
- UI readiness: PASS
- sidecar shutdown: PASS
- final port residue: none

The app remains unsigned and `spctl` reports `rejected` with
`no usable signature`. No Gatekeeper bypass was used.

The temporary install directory was inside workspace-dev, so the app still
resolved the workspace-known onedir sidecar. Formal DMG work must place the
complete onedir sidecar tree inside App Bundle resources before independent
clean-machine distribution testing.

See `DMG_SMOKE_REPORT.md`.

## DMG Portable Independence Follow-Up

Generated: 2026-06-03

The complete onedir sidecar tree is now included in App Bundle resources.

The packaged launcher selected:

```text
bundled_onedir_resource
```

An isolated app copy outside workspace-dev passed health, UI readiness,
shutdown, and no-residue checks. `/api/health` and desktop main logs did not
contain the workspace-dev path.

Result: **PASS**

The Tauri artifact is now a locally movable unsigned macOS app prototype.
