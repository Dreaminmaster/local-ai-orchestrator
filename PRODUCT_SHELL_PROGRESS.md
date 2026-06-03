# Product Shell Progress

Generated: 2026-06-02T17:05:30+08:00

## Scope

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

This phase stops chasing Claude Workspace live auto-PASS and treats External AI workspace instability as a product state: detect, pause, guide the user, then resume.

No live Claude run was executed in this phase.

## Completed Product Shell Capabilities

### Pending External AI Action

When WebAISkill sees a resumable provider state such as `NEED_LOGIN` or `NEED_USER_INTERVENTION`, it saves:

`runtime/tasks/{task_id}/pending_external_ai.json`

Payload includes:

- `task_id`
- `step_id`
- `provider`
- `original_prompt`
- `redacted_prompt`
- `context`
- `provider_status`
- `failure_reason`
- `suggested_user_action`
- `can_resume`
- `created_at`

### Resume API

Added:

- `GET /api/external-ai/pending`
- `POST /api/external-ai/{task_id}/resume`

Resume behavior:

- Rechecks provider status before sending.
- If provider still needs user action, returns `still_needs_user=true` and does not send.
- If provider is `READY`, `PASS`, or `PARTIAL`, re-executes the pending WebAISkill action.
- Saves result to `runtime/tasks/{task_id}/pending_external_ai_result.json`.
- Returns `resume_payload` so the frontend can continue the original task.

### Agent Events

External AI pause/resume event types:

- `external_ai_need_user`
- `external_ai_pending_saved`
- `external_ai_resume_started`
- `external_ai_resume_success`
- `external_ai_resume_still_needs_user`
- `external_ai_resume_failed`

When a task hits a pending External AI action, Agent saves StepState and pauses instead of entering ordinary failure repair.

### Frontend Product Shell

Top system status:

- Backend
- Portable mode
- LM Studio
- Current task

Task pause area:

- Shows External AI pause reason.
- Provides “我已处理，继续”.
- Provides “查看待处理外部 AI 动作”.
- Provides “重新检测”.

External AI Workspace panel:

- Claude / ChatGPT workspace rows.
- Open workspace.
- Recheck.
- Test.
- I handled it, continue.
- Reset profile.
- View evidence.

Provider state copy:

- `READY`: 可用
- `PASS`: 已测试通过
- `PARTIAL`: 可用但不稳定
- `NEED_LOGIN`: 需要登录
- `NEED_USER_INTERVENTION`: 需要你处理
- `FAIL`: 测试失败
- `NOT_CONFIGURED`: 未配置

## Is The External AI Intervention Resume Loop Complete?

Status: **offline product-loop complete**

The code now supports:

- Saving pending External AI work.
- Showing user-facing pause state.
- Rechecking provider readiness.
- Avoiding send when still logged out or blocked.
- Resuming pending action when provider is ready.
- Returning a task resume payload.

Live Claude remains intentionally outside this phase.

## Why This Is Not Yet A Formal Desktop App

- No Tauri shell has been built.
- No signed macOS app bundle, DMG, EXE, or MSI exists.
- Portable dependencies are not provisioned inside this workspace-dev clone.
- Claude/ChatGPT login is still browser-profile based and user-managed.
- UI is now a product shell, but not yet packaged as a desktop application.

## Non-Live Checks

- `scripts/health_check.py`: PASS.
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10.
- `node --check frontend/app.js`: PASS.
- `tests/test_pending_external_ai_resume.py`: PASS, 3 tests.
- `tests/test_workspace_login_state.py`: PASS, 6 tests.
- `tests/test_beta_validation_status.py`: PASS, 1 test.
- `tests/test_workspace_recovery.py`: PASS, 6 tests.
- `tests/test_answer_quality_check.py`: PASS, 2 tests.
- `tests/test_claude_answer_extractor_from_evidence.py`: PASS, 4 tests.
- `scripts/beta_validation.py`: PASS, live Claude skipped.

## Next Step

Ready to enter **Tauri sidecar dev** after deciding packaging scope:

- Bundle backend as sidecar.
- Preserve portable runtime paths.
- Keep browser profiles under `runtime/browser_profiles/`.
- Keep evidence and reports under `runtime/`.
- Do not package or commit user runtime data.

## Tauri Dev Shell Update

Dev shell files are now present under `apps/desktop/`:

- `package.json`
- `src-tauri/Cargo.toml`
- `src-tauri/tauri.conf.json`
- `src-tauri/src/main.rs`
- `src-tauri/capabilities/default.json`
- `src-tauri/run_dev_backend.sh`
- `run_dev.sh`
- `run_dev_windows.ps1`
- `README.md`

Current status:

- `devUrl=http://127.0.0.1:8422`.
- `bundle.active=false`.
- `/api/health` route has been added in code.
- Frontend top status reads `/api/health`.
- Tauri dev smoke is blocked locally because Rust/Cargo/Tauri CLI are missing.
- No global install was attempted.

Detailed report:

`TAURI_DEV_SHELL_REPORT.md`

## Web Product Shell Health Verification

Latest local verification:

- Old backend stopped: yes, PID `50920` from `/Users/johnwick/Documents/codex/local-ai-orchestrator-main`.
- Workspace-dev backend started: yes, PID `55671`.
- Backend cwd: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`.
- `/api/health`: PASS, returned `"ok": true`.
- Frontend top system status reads `/api/health`: PASS.
- Displayed frontend health state:
  - Backend: `running`
  - Portable mode: `OK`
  - LM Studio: `disconnected`
  - External AI: `Claude READY / ChatGPT NOT_CONFIGURED`
  - Desktop Shell: `browser mode`
  - Current task: `external_ai_manual`
- Frontend screenshot: `runtime/test_reports/web_product_shell_health.png`.

Requested non-live checks:

- `scripts/health_check.py`: PASS.
- `scripts/beta_validation.py`: PASS, live Claude skipped.
- `node --check frontend/app.js`: PASS.

Status: ready to ask for Rust/Tauri dev environment installation confirmation. No Rust, Cargo, Tauri CLI, or global dependency install was attempted.

## Tauri Dev Smoke Result

Generated: 2026-06-02T21:23:00+08:00

This run did not install Rust, did not install global Tauri CLI, did not run live Claude, and did not test other providers.

What succeeded:

- `apps/desktop/npm install`: PASS.
- Dependencies were installed only under `apps/desktop/node_modules`.
- Project-local `@tauri-apps/cli`: available.
- Project-local Tauri CLI version: `tauri-cli 2.11.2`.
- `apps/desktop/package-lock.json`: generated and should be committed for reproducible desktop dev dependencies.
- Backend `/api/health`: PASS, `"ok": true`.
- Backend duplication check: PASS, only existing PID `55671` was listening on `8422`.
- `node --check frontend/app.js`: PASS.
- Borrowed old success venv with `PYTHONPATH` pointing to workspace-dev:
  - `scripts/health_check.py`: PASS.
  - `scripts/beta_validation.py`: PASS, live Claude skipped.

What is blocked:

- `rustc --version`: command not found in current shell.
- `cargo --version`: command not found in current shell.
- `npm run dev`: blocked because Tauri could not run `cargo metadata`.
- Tauri desktop window did not open.
- WebView did not load `http://127.0.0.1:8422` because the Tauri process exited before launch.

Backend shutdown result:

- Tauri dev did not start its own backend.
- No duplicate backend was created.
- The pre-existing workspace-dev backend remains running as PID `55671`.
- No unrelated Python process was killed.

Current readiness:

- Not ready for Python backend sidecar binary design yet.
- First resolve Rust/Cargo visibility in the active shell, then rerun Tauri dev smoke.
- After Tauri WebView successfully opens and backend lifecycle behavior is verified, the project can enter Python backend sidecar binary design.

## Tauri Dev Smoke With FlyEnv Rust

Generated: 2026-06-02T21:48:00+08:00

Rust/Cargo were provided by FlyEnv for the current command only:

- `rustc 1.96.0 (ac68faa20 2026-05-25)`
- `cargo 1.96.0 (30a34c682 2026-05-25)`
- `rustc`: `/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin/rustc`
- `cargo`: `/Users/johnwick/Library/FlyEnv/app/rust-1.96.0/bin/cargo`

Tauri dev smoke result: PASS.

What was verified:

- Project-local Tauri CLI was used.
- No global Tauri CLI was installed.
- `npm run dev` completed Rust dev compilation.
- Tauri launched `target/debug/local-ai-orchestrator-desktop`.
- Existing backend on port `8422` was detected as healthy and reused.
- No duplicate backend remains.
- `/api/health` returned `"ok": true`.

Small dev shell fixes made:

- Fixed Tauri `beforeDevCommand` script path.
- Hardened backend reuse logic in `run_dev_backend.sh`.
- Added a minimal development icon required by Tauri context generation.

Current running processes:

- Tauri dev node process: PID `99828`.
- Tauri desktop app process: PID `99929`.
- Backend process: PID `55671`.

Generated local development artifacts:

- `apps/desktop/node_modules/`
- `apps/desktop/package-lock.json`
- `apps/desktop/src-tauri/target/`

Do not commit:

- `apps/desktop/node_modules/`
- `apps/desktop/src-tauri/target/`
- `runtime/`
- `venv/`
- `.env`
- `.playwright-browsers/`

Commit candidate:

- `apps/desktop/package-lock.json`
- `apps/desktop/src-tauri/tauri.conf.json`
- `apps/desktop/src-tauri/run_dev_backend.sh`
- `apps/desktop/src-tauri/icons/icon.png`

Readiness:

- The project can now enter Python backend sidecar binary design.
- It is still not a formal desktop installer because no sidecar binary, packaging, signing, notarization, updater, DMG, EXE, or MSI work has been done.

## Backend Binary Prototype

Generated: 2026-06-02T23:21:00+08:00

Status: PASS.

Completed:

- Created `.build-venv` under workspace-dev.
- Installed project requirements into `.build-venv`.
- Installed PyInstaller into `.build-venv`.
- Built backend binary prototype with PyInstaller.
- Added sidecar CLI entry: `backend/sidecar_entry.py`.
- Added build script: `scripts/build_backend_binary.py`.
- Added `LOCAL_AI_BACKEND_MODE=python|binary` support to `run_dev_backend.sh`.

Binary:

- Path: `apps/desktop/src-tauri/bin/local-ai-orchestrator-backend`.
- Size: about `74M`.
- `--version`: PASS.
- `--health-check-only`: PASS.
- Direct `/api/health`: PASS.

Tauri binary backend mode:

- `LOCAL_AI_BACKEND_MODE=binary`: PASS.
- Tauri launched the backend binary.
- WebView loaded the product UI.
- `/api/health` returned `"ok": true`.
- No duplicate backend remained.
- Closing Tauri stopped the binary backend it started.

Existing backend reuse:

- PASS.
- Tauri reused a manually started healthy Python backend.
- Closing Tauri did not kill that manually started backend.

Non-live checks:

- `.build-venv/bin/python scripts/health_check.py`: PASS.
- `.build-venv/bin/python scripts/beta_validation.py`: PASS, live Claude skipped.
- `node --check frontend/app.js`: PASS.

Still not a formal installer:

- No `tauri build`.
- No `bundle.externalBin` final packaging.
- No DMG/EXE/MSI.
- No signing.
- No notarization.
- No updater.
- Playwright browsers are not packaged.
- Runtime location for installed apps is not finalized.

Readiness:

- Ready to enter formal sidecar bundle design.

## Formal Sidecar Bundle Design

Generated: 2026-06-02T23:35:00+08:00

Status: design complete, implementation not started.

Added:

- `FORMAL_SIDECAR_BUNDLE_PLAN.md`

Key decisions:

- Keep runtime data out of the app bundle.
- Keep browser profiles, evidence, reports, `.env`, and local DB files out of the bundle.
- Do not automatically package Playwright browsers yet.
- Use app data directory for installed runtime in a later phase.
- Use Tauri `externalBin` with target-triple sidecar naming in a later phase.
- Keep capabilities minimal and do not expose arbitrary shell execution.

Current recommendation:

- Do not run formal `tauri build` yet.
- Next stage should be formal sidecar bundle pre-build preparation:
  - target-triple sidecar naming
  - installed runtime path implementation
  - app data settings model
  - Playwright browser provisioning UX
  - sidecar permission review

## v0.2.3 Formal Sidecar Build Prep

Generated: 2026-06-03T00:00:00+08:00

Completed:

- Host target triple checked with FlyEnv Rust: `x86_64-apple-darwin`.
- Target-triple sidecar preparation script added.
- Tauri config now reserves `bundle.externalBin=[]` while keeping `bundle.active=false`.
- Runtime path model added for dev/custom/installed modes.
- Non-secret `settings.json` store added.
- Playwright browser provisioning status API added.
- Frontend project browser status section added.
- Tauri capability review remains minimal: `core:default` only.

Still not done:

- no `tauri build`
- no DMG/EXE/MSI
- no signing or notarization
- no updater
- no automatic Playwright browser provisioning
- no committed backend binary

## Tauri Build Smoke Update

Generated: 2026-06-03T01:30:00+08:00

Progress:

- `aarch64-apple-darwin` sidecar naming issue fixed.
- Tauri `.app` build completed successfully.
- `.app` launches the desktop process and bundled backend sidecar.
- Packaged sidecar reaches Uvicorn and logs `/api/health` `200 OK`.
- App data runtime path is used instead of project `runtime/`.

Still partial:

- packaged health probe now has hard timeouts and no longer relies on a curl loop.
- frontend readiness marker and `/api/ui-ready` were added.
- normal app quit cleanup passed for the app-started sidecar PID.
- latest packaged PyInstaller onefile sidecar did not reach Uvicorn within 180 seconds.
- WebView UI readiness remains blocked by sidecar startup reliability.

Current status:

- Tauri build: PASS.
- Runtime smoke: PARTIAL.
- Not ready to tag/sync as a stable build-smoke milestone yet.

## Onedir Packaged Sidecar Diagnostic

Generated: 2026-06-03

Completed:

- Backend build script supports `--mode onefile` and `--mode onedir`.
- Onedir backend directly reaches Uvicorn and `/api/health`.
- Packaged Tauri launcher records sidecar command, arguments, environment,
  working directory, PID, stdout path, and stderr path.
- Packaged Tauri launcher selected the workspace-known onedir executable.
- Packaged onedir sidecar reached `/api/health`.
- Packaged onedir sidecar shut down gracefully on app exit.
- Final port `8422` and packaged process checks were clean.

Current conclusion:

- Onefile is not recommended as the current v0.2.x packaged sidecar prototype.
- Onedir is the recommended backend sidecar direction for the next prototype.
- Overall packaged runtime smoke remains PARTIAL because the WebView did not
  report the UI readiness marker before the desktop process exited.
- The next focused task is WebView load/navigation timing, not provider work or
  backend sidecar startup.
- This state is not ready for GitHub sync, tag, unsigned macOS app prototype,
  or formal installer work.

## Unsigned macOS App Prototype Readiness

Generated: 2026-06-03

The final packaged runtime smoke passed after removing the unnecessary WebView
navigation to the frozen backend root. The Tauri bundled frontend now remains
loaded while it calls the sidecar API on localhost.

Verified:

- Tauri build: PASS
- packaged onedir sidecar: PASS
- backend `/api/health`: PASS
- WebView created: PASS
- frontend readiness POST: PASS
- health panel rendered: PASS
- desktop shell mode reported as `packaged / tauri`
- app-owned sidecar shutdown: PASS
- final `8422` listener: none
- final runtime smoke: PASS

Current status:

- Ready to enter unsigned macOS app prototype planning.
- Ready to prepare a synchronization checkpoint.
- Not ready for DMG, signing, notarization, updater, or formal release.

## Unsigned DMG Smoke

Generated: 2026-06-03

Result: **PASS**

Verified:

- unsigned DMG generated with `hdiutil`
- DMG mounted successfully
- `.app` and Applications symlink present
- app copied to a temporary Applications test directory
- copied app launched
- onedir sidecar started
- `/api/health` passed
- UI readiness and health panel rendering passed
- app-owned sidecar exited
- port `8422` had no residue
- DMG and temporary install cleanup completed

Security result:

- app is not signed
- `spctl` rejected it with `no usable signature`
- no Gatekeeper bypass or system security change was performed

Prototype limitation:

- the temporary install path remained inside workspace-dev
- the copied app still used the workspace-known onedir sidecar
- formal DMG design must bundle the complete onedir tree inside App resources

The product shell can enter formal DMG design, but not formal release.

## DMG Portable Independence

Generated: 2026-06-03

Result: **PASS**

- complete onedir backend sidecar bundled inside App resources
- isolated app copy launched outside workspace-dev
- packaged launcher used `bundled_onedir_resource`
- project root, runtime, settings, database, and Playwright paths use app data
- health and main logs contained no workspace-dev dependency
- UI readiness passed
- sidecar shutdown passed
- port `8422` had no residue

Current status:

- locally movable unsigned DMG prototype: ready
- formal DMG release preparation: ready
- signing, notarization, updater, and public release: not started

## First Run Experience And Local Support

Generated: 2026-06-03

Completed:

- API-driven first run status page
- app data status and open-directory actions
- diagnostics package export
- conservative cache cleanup
- explicit provider profile reset confirmation
- Playwright browser missing notice without automatic download
- packaged app smoke for health, UI readiness, diagnostics, cleanup, and
  sidecar shutdown

Current status:

- user-testable unsigned DMG: ready
- terminal-free first run support: available
- formal public release: not ready
