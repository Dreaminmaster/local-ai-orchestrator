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
