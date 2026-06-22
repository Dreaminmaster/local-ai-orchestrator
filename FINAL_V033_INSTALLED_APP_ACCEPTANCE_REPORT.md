# Final v0.3.3 Installed App Acceptance Report

Date: 2026-06-22

## Status

PASS

## Installed Main App

`/Applications/Local AI Orchestrator.app`

This installed App was copied from:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.3-arm64-full-tauri-generic-repair-workspace-reuse-unsigned.dmg`

SHA-256:

`d42ead9ec6d6f3de2d39bdc7a98bac7be5dea25f4fb986e3afb3e69705bc2749`

## Previous Main App Backup

The previous `/Applications/Local AI Orchestrator.app` was moved, not deleted:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/old-apps/Local AI Orchestrator-20260622_193324.app`

## Startup Smoke

- App launch: PASS
- `/api/health`: PASS
- `/api/ui-ready`: PASS
- LM Studio detection: PASS, `READY` / `VERIFIED`
- Ollama state: disabled/skipped by user
- Provider Console API: PASS
- app-data runtime path: PASS
- packaged frontend readiness: PASS

## Architecture

Installed App audit:

- Result: PASS
- Mach-O count: 84
- x86_64-only count: 0
- Tauri main executable: arm64
- backend sidecar: arm64

Audit output:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/v033_installed_app_arch_audit.json`

## Packaged Generic Repair

Installed-App packaged smoke:

- `print(message)` NameError repair: PASS
- local ImportError repair: PASS
- `compileall` PASS but real entry FAIL false-success prevention: PASS

## Packaged Workspace Reuse

No live provider prompt was sent.

Claude:

- second open reused existing workspace: PASS
- same window focused: PASS
- second context created: false

Kimi:

- second open reused existing workspace: PASS
- same window focused: PASS
- second context created: false

## Realtime / Final Report

- async real-project task: PASS
- event history observed: PASS, 39 events
- final report available: PASS
- task completed: PASS

## Shutdown

- App quit: PASS
- sidecar exited: PASS
- 8422 listener residue: none
- 8423 listener residue: none
- DMG detach: PASS

## Conclusion

v0.3.3 is installed as the current `/Applications` main App and is suitable as the current main self-use version.
