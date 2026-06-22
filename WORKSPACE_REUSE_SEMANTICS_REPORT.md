# Workspace Reuse Semantics Report

Date: 2026-06-21

## Summary

Status: PASS

Provider workspace repeated-open semantics were corrected without changing the single-owner architecture.

## Implemented

- Added stable `workspace_id` separate from per-click `request_id`.
- Added explicit response fields:
  - `workspace_already_open`
  - `workspace_reused`
  - `new_context_created`
  - `second_context_created`
  - `same_window_focused`
  - `last_focused_at`
- Reopening an already open provider workspace now focuses the existing page instead of reporting a new workspace launch.
- The open API now treats an already `READY`, `OPEN`, or `BUSY` workspace as focus/reuse, while `OPENING` returns the in-progress state.
- Provider Console UI now displays workspace id, opened/focused timestamps, reuse state, focused state, and context creation state.

## Expected Repeated Open Response

```json
{
  "workspace_already_open": true,
  "workspace_reused": true,
  "second_context_created": false,
  "new_context_created": false,
  "same_window_focused": true
}
```

`request_id` remains per API request. `workspace_id` is the stable workspace/session identifier.

## Verification

Commands:

```bash
PYTHONPATH=. .build-venv/bin/python -m unittest tests/test_external_ai_workspace_single_owner.py tests/test_workspace_open_product_flow.py
PYTHONPATH=. .build-venv/bin/python scripts/e2e_provider_workspace_console.py
```

Results:

- Claude first open/second open semantics: PASS.
- Kimi second open semantics: PASS.
- Busy workspace does not create second context: PASS.
- Concurrent open requests create one browser context: PASS.
- Provider Console API smoke: PASS.
- 8422/8423 residue after temporary backend test: none.

## Live Prompt Safety

No live provider prompt was sent in this sprint.

## v0.3.2 Packaged Smoke

- Claude second open in packaged App: `workspace_reused=true`, `same_window_focused=true`, `second_context_created=false`.
- Kimi second open in packaged App: `workspace_reused=true`, `same_window_focused=true`, `second_context_created=false`.
- No live provider prompt was sent.
