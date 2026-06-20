# Changed Files Manifest

## External AI Workspace And Task Resume

- `backend/api/external_ai_actions.py`
- `backend/api/web_ai_profiles.py`
- `backend/core/agent.py`
- `backend/local_model/external_ai_escalation.py`
- `backend/skills/external_ai_web/pending_action.py`
- `backend/skills/external_ai_web/provider_status.py`
- `backend/skills/external_ai_web/workspace_manager.py`
- `backend/skills/external_ai_web/web_ai_skill.py`
- `backend/skills/external_ai_web/claude_web_adapter.py`
- `backend/skills/external_ai_web/answer_extractor.py`
- `backend/skills/external_ai_web/answer_quality_check.py`

## Runtime, Settings, Health, And Playwright Status

- `backend/main.py`
- `backend/api/app_data.py`
- `backend/api/health.py`
- `backend/api/playwright_status.py`
- `backend/runtime_paths.py`
- `backend/settings_store.py`
- `backend/sidecar_entry.py`

## Frontend Product Shell

- `frontend/index.html`
- `frontend/app.js`
- `frontend/style.css`
- `docs/web_ai_test_matrix.md`

## Tauri Desktop Shell And Sidecar

- `apps/desktop/package-lock.json`
- `apps/desktop/README.md`
- `apps/desktop/run_dev.sh`
- `apps/desktop/run_dev_windows.ps1`
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/src-tauri/Cargo.lock`
- `apps/desktop/src-tauri/capabilities/default.json`
- `apps/desktop/src-tauri/icons/icon.png`
- `apps/desktop/src-tauri/run_dev_backend.sh`
- `apps/desktop/src-tauri/src/main.rs`
- `apps/desktop/src-tauri/tauri.conf.json`

## Scripts

- `scripts/beta_validation.py`
- `scripts/build_backend_binary.py`
- `scripts/e2e_claude_workspace_live.py`
- `scripts/prepare_tauri_sidecar_binary.py`
- `scripts/tauri_packaged_runtime_smoke.py`
- `8_运行Beta验收.command`
- `8_运行Beta验收.bat`

## Tests

- `tests/test_answer_quality_check.py`
- `tests/test_app_data_diagnostics.py`
- `tests/test_beta_validation_status.py`
- `tests/test_claude_answer_extractor_from_evidence.py`
- `tests/test_pending_external_ai_resume.py`
- `tests/test_runtime_paths_settings_playwright.py`
- `tests/test_workspace_login_state.py`
- `tests/test_workspace_recovery.py`

## Reports And Design Documents

- `BACKEND_BINARY_PROTOTYPE_REPORT.md`
- `BETA_VALIDATION_REPORT.md`
- `DMG_PREP_PLAN.md`
- `DMG_INDEPENDENCE_SMOKE_REPORT.md`
- `DMG_SMOKE_REPORT.md`
- `FIRST_RUN_EXPERIENCE_REPORT.md`
- `FORMAL_SIDECAR_BUNDLE_PLAN.md`
- `FORMAL_SIDECAR_PREP_REPORT.md`
- `PRODUCT_SHELL_PROGRESS.md`
- `PYTHON_SIDECAR_BINARY_DESIGN.md`
- `RELEASE_DMG_PREP_PLAN.md`
- `TAURI_BUILD_SMOKE_REPORT.md`
- `TAURI_DEV_SHELL_REPORT.md`
- `TAURI_INSTALL_PLAN.md`
- `WORKSPACE_DEV_BASELINE_CHECK.md`

## Explicitly Excluded Local Or Generated Data

- `backend/storage/orchestrator.db`
- `apps/desktop/src-tauri/gen/`
- `.build-venv/`
- `runtime/`
- `venv/`
- `.env`
- `.playwright-browsers/`
- browser profiles
- evidence
- local test reports
- `node_modules/`
- `target/`
- `.app`
- DMG files
- backend binary files
