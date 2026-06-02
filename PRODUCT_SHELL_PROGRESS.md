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
