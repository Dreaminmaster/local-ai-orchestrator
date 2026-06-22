# Moved Files Manifest

Date: 2026-06-20

## Archive Root

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612`

## Current Archive Layout

- Patches: `patches/`
- Backups: `backups/`
- Generated artifacts: `generated-artifacts/`
- Temporary build and smoke staging: `staging/`
- Test workspaces: `test-workspaces/`

## New Final Artifact

`generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-unsigned.dmg`

## Provider Console Arm64 Rebuild Artifact

`generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-provider-console-unsigned.dmg`

- Size: `176017936` bytes
- SHA-256: `a3da1f80e76d7efaf4e16d69b712529c77c2d56a96273cec7e3b9a80c4ad50a8`
- Purpose: arm64 unsigned self-use DMG containing Provider Workspace Console, short-answer extraction fixes, and ImportError runtime-entry verification fixes.

Supporting files:

- `patches/provider_workspace_console_arm64_rebuild.patch`
- `backups/provider_workspace_console_arm64_rebuild_local_backup.zip`
- `staging/provider-console-arm64-build/`
- `test-workspaces/provider-console-arm64-install-smoke/`

Old main artifact moved, not deleted:

- `generated-artifacts/old/Local-AI-Orchestrator-final-complete-arm64-unsigned.dmg`

## Final Installed App Acceptance - 2026-06-21

Installed main App:

- `/Applications/Local AI Orchestrator.app`

Old `/Applications` App moved, not deleted:

- `old-apps/Local AI Orchestrator-20260621_160330.app`

Current installed-acceptance evidence:

- `staging/final-installed-app-acceptance/`
- `test-workspaces/final-installed-app-acceptance/`
- `test-workspaces/final-installed-app-acceptance-supported/`
- `test-workspaces/final-installed-app-acceptance-small-project/`

Older test workspaces moved, not deleted:

- `test-workspaces/old/final-real-machine-acceptance-20260621_161137/`
- `test-workspaces/old/provider-console-arm64-install-smoke-20260621_161137/`
- `test-workspaces/old/provider-console-repair-verification-20260621_161137/`

## New Apple Silicon Staging Artifacts

`staging/apple-silicon-rebuild/`

Contains architecture audit JSON/Markdown, smoke payload summaries, rollback result, and the isolated arm64 Rust toolchain used for this local rebuild.

## Files Intentionally Not Archived As Source

- `.build-venv/`
- `runtime/`
- `.playwright-browsers/`
- `.env`
- browser profiles
- evidence contents
- `apps/desktop/node_modules/`
- `apps/desktop/src-tauri/target/`
- generated `.app`
- generated backend binaries

## Codex Root Hygiene

This sprint used the existing archive root and did not intentionally create new deliverables directly under `/Users/johnwick/Documents/codex`.

## Final Cleanup 2026-06-20

- Cleanup plan: CLEANUP_PLAN_FINAL.md
- Cleanup report: FINAL_CLEANUP_REPORT.md
- Move log: /Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/apple-silicon-rebuild/final-cleanup-move-log-20260620_214953.tsv
- Moved to old/: 63 items
- Permanently deleted: 0 items
- Final arm64 DMG preserved: yes
- Final patch preserved: yes
- Final backup preserved: yes
## v0.3.2 Generic Repair & Workspace Reuse - 2026-06-21

- Patch: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/patches/generic_repair_workspace_reuse_v032.patch`
- Backup: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/backups/generic_repair_workspace_reuse_v032_local_backup.zip`
- DMG: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.2-arm64-generic-repair-workspace-reuse-unsigned.dmg`
- Reports:
  - `GENERIC_REPAIR_EXPANSION_REPORT.md`
  - `WORKSPACE_REUSE_SEMANTICS_REPORT.md`
  - `FINAL_V032_ARM64_DMG_REPORT.md`
  - `FINAL_V032_INSTALL_SMOKE_REPORT.md`
- Excluded from sync/archive package: runtime data, profiles, evidence, generated app bundles, DMG internals, node_modules, target, `.build-venv`, backend binary, and Playwright browser payloads.

## v0.3.3 Full Tauri Rebuild - 2026-06-22

- Patch: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/patches/full_tauri_v033_generic_repair_workspace_reuse.patch`
- Backup: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/backups/full_tauri_v033_generic_repair_workspace_reuse_local_backup.zip`
- DMG: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.3-arm64-full-tauri-generic-repair-workspace-reuse-unsigned.dmg`
- Reports:
  - `TEMP_RUST_TOOLCHAIN_BUILD_REPORT.md`
  - `FINAL_V033_FULL_TAURI_REBUILD_REPORT.md`
  - `FINAL_V033_INSTALL_SMOKE_REPORT.md`
- Staging/test evidence retained under archive root:
  - `staging/v033_dmg_arch_audit.json`
  - `staging/v033_copied_app_arch_audit.json`
  - `staging/v033-packaged-api-smoke.json`
  - `staging/v033-packaged-realtime-smoke.json`
  - `test-workspaces/v033-install-smoke/`
  - `test-workspaces/v033-packaged-api-smoke/`
  - `test-workspaces/v033-realtime-smoke/`
- Excluded from backup/package: DMG, `.app`, runtime data, profiles, cookies, evidence contents, node_modules, target, `.build-venv`, backend binary, Playwright browsers, and temporary Rust toolchain.

## v0.3.3 Installed Main App - 2026-06-22

- Installed App: `/Applications/Local AI Orchestrator.app`
- Previous App backup: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/old-apps/Local AI Orchestrator-20260622_193324.app`
- Current main DMG retained:
  `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.3-arm64-full-tauri-generic-repair-workspace-reuse-unsigned.dmg`
- Moved old DMGs to `generated-artifacts/old/`:
  - `Local-AI-Orchestrator-final-complete-arm64-provider-console-unsigned.dmg`
  - `Local-AI-Orchestrator-v0.3.2-arm64-generic-repair-workspace-reuse-unsigned.dmg`
- Installed acceptance report: `FINAL_V033_INSTALLED_APP_ACCEPTANCE_REPORT.md`
- Installed architecture audit: `staging/v033_installed_app_arch_audit.json`
- Installed packaged smoke: PASS
