# Final v0.3.3 Install Smoke Report

Date: 2026-06-22

## Status

PASS

## Artifact

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.3-arm64-full-tauri-generic-repair-workspace-reuse-unsigned.dmg`

SHA-256:

`d42ead9ec6d6f3de2d39bdc7a98bac7be5dea25f4fb986e3afb3e69705bc2749`

## Isolated Install Smoke

DMG mount:

- Mounted: PASS
- DMG App exists: PASS

Copied App:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/test-workspaces/v033-install-smoke/Applications/Local AI Orchestrator.app`

Checks:

- copied App architecture audit: PASS
- App launch: PASS
- `/api/health`: PASS
- `/api/ui-ready`: PASS
- app-data runtime path: PASS
- no workspace-dev runtime dependency: PASS

## Packaged Generic Repair Smoke

Result file:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/v033-packaged-api-smoke.json`

Cases:

- `print(message)` NameError: PASS
- local ImportError module-name mismatch: PASS
- `compileall` PASS but runtime import FAIL: PASS as false-success prevention, final status remained failed

## Packaged Workspace Reuse Smoke

No live provider prompt was sent.

Claude:

- first open state: READY
- second open state: READY
- stable workspace_id reused: PASS
- same window focused: PASS
- new context created on second open: false
- second context created: false

Kimi:

- first open state: READY
- second open state: READY
- stable workspace_id reused: PASS
- same window focused: PASS
- new context created on second open: false
- second context created: false

## Realtime / Final Report Smoke

Result file:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/v033-packaged-realtime-smoke.json`

Checks:

- async task created: PASS
- realtime event history: PASS, 39 events
- terminal event observed: PASS
- final report available: PASS
- repair flow event sequence: PASS
- final status: PASS

## Shutdown

- App quit: PASS
- sidecar exited: PASS
- 8422 listener residue: none
- 8423 listener residue: none
- DMG detach: PASS

## Conclusion

The v0.3.3 full Tauri arm64 unsigned DMG is suitable as the next main self-use candidate, pending user confirmation before replacing the installed `/Applications/Local AI Orchestrator.app`.
