# Beta Kernel Validation

Checked on: 2026-06-02

Portable mode verified. Claude Web live E2E PASS. ChatGPT Web PARTIAL (fallback).

## Portable Deployment

All project artifacts in `local-ai-orchestrator/`:

- `venv/` — Python virtual environment
- `.playwright-browsers/` — Chromium (portable, not system)
- `runtime/` — Evidence, test reports, browser profiles, logs

No system dependency installation required.

## Web AI Providers

| Provider | Status | Notes |
|---|---:|---|
| Claude Web | ✅ PASS | Preferred escalation provider |
| ChatGPT Web | ⚠️ PARTIAL | Fallback; extraction uses body_fallback |

## Agent E2E — Claude Web

Script: `scripts/e2e_agent_uses_claude_web.py`

Chain: failure → escalation → Claude Web → answer → evidence → report

Result: PASS

## Repair Matrix

Script: `scripts/e2e_agent_driven_repair_matrix.py`
Result: 10/10 PASS

## Files To Push

See commit for full diff. Key changes:

- Claude Web preferred escalation provider
- ChatGPT PARTIAL fallback handling
- Claude answer extraction with body_marker
- Web AI evidence writer per-provider directory
- Claude Web / claude_web alias in WebAISkill
- Claude answer extractor unit test
- Web UI recommended provider badge

## Files NOT To Push

- `venv/`, `.playwright-browsers/`, `runtime/`
- `.env`
- `LOCAL_INSTALL_AUDIT.md` (contains local paths)
