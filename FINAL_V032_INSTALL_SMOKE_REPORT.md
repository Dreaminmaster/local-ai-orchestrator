# Final v0.3.2 Install Smoke Report

Date: 2026-06-21

## Result

Status: PASS

## DMG

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-v0.3.2-arm64-generic-repair-workspace-reuse-unsigned.dmg`

SHA-256:

`42bb1267cffcd833d306f35fb06786b036782f275c9df8c5fe3e9f1ea24f578f`

## Install Smoke

- DMG mounted: PASS.
- App copied to isolated test directory: PASS.
- App launched from isolated copy: PASS.
- `/api/health`: PASS.
- `/api/ui-ready`: PASS.
- LM Studio detection: READY / VERIFIED.
- Ollama: DISABLED / skipped.
- App data runtime path: user App Support directory.
- Sidecar startup: PASS.
- Sidecar shutdown: PASS.
- 8422 residue: none.
- 8423 residue: none.

## Packaged Generic Repair Smoke

API smoke file:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/v032-packaged-api-smoke.json`

Results:

- `print(message)` NameError repair: PASS.
- Wrong local import repair: PASS.
- `compileall` PASS but runtime import FAIL: correctly FAILED, no false success.
- Final reports generated in App Data runtime task directories: PASS.

## Packaged Workspace Reuse Smoke

- Claude first open / second open: PASS.
- Claude `workspace_id` stable: PASS.
- Claude `workspace_reused=true`: PASS.
- Claude `same_window_focused=true`: PASS.
- Claude `second_context_created=false`: PASS.
- Kimi first open / second open: PASS.
- Kimi `workspace_id` stable: PASS.
- Kimi `workspace_reused=true`: PASS.
- Kimi `same_window_focused=true`: PASS.
- Kimi `second_context_created=false`: PASS.

No live provider prompt was sent.

## Product Core Smoke

Command:

```bash
PYTHONPATH=. .build-venv/bin/python scripts/e2e_product_core.py
```

Result: PASS

- File create/read/report task: PASS.
- Shell task: PASS.
- NameError repair task: PASS.
- Pending external AI simulation: PASS.
- Final report generation: PASS.
