# External AI Workspace Single-Owner Report

Updated: 2026-06-12

## Result

**Single-owner workspace: PASS**

The backend `WorkspaceManager` is now the only owner allowed to open project
persistent browser profiles. Agent code, UI actions, provider tests, profile
initialization, and Claude live E2E use backend APIs rather than opening a
second Playwright context.

## Root Cause And Fix

The previous live attempt failed because the backend and an independent E2E
process both tried to open `runtime/browser_profiles/claude/`.

The repaired flow is:

`UI / Agent / E2E -> backend API -> WorkspaceManager -> one context/page -> adapter`

- Profile owner: `backend`
- Second browser context: `false`
- Claude request queue: one `asyncio.Lock` per provider
- Workspace lifetime: stays open until explicit close, profile reset, app
  shutdown, or crash recovery
- Packaged App: uses the same bundled backend-sidecar ownership model

## Ownership Diagnostics

An active workspace writes:

`runtime/browser_profiles/<provider>/.workspace-owner.json`

It contains only provider, backend PID, owner type, timestamps, profile path,
and app instance ID. It contains no cookies, credentials, account data, or page
content. Normal close and App shutdown remove the owner record. A dead PID is
recognized as stale and can be recovered.

## Backend API

Unified local endpoint:

`POST /api/external-ai/workspaces/{provider}/ask`

The endpoint returns ownership, reuse, request, send, extraction, quality,
evidence, and intervention fields. It never creates a second profile context.

## Offline Validation

- Single-owner focused tests: **10/10 PASS**
- Workspace/login/recovery/pending/quality/extractor tests: **31/31 PASS**
- Agent repair matrix: **10/10 PASS**
- Health check: **PASS**
- Beta validation: **PASS**, live skipped
- Frontend syntax: **PASS**
- Full unittest discovery: **55 tests PASS**, one existing OCR module could not
  import because `.build-venv` does not contain `pytest`; no dependency was
  installed.

## Controlled Live Result

- Claude minimal live: **SKIPPED before prompt send**
- Agent uses Claude live: **SKIPPED**
- Live prompt total: **0**
- Other providers called: **none**

The controlled run stopped during backend API preflight. Uvicorn started, but
the E2E process's `urllib` health request was affected by proxy handling and did
not reach `127.0.0.1`. Local API helpers now explicitly bypass proxies, and a
non-live backend `/api/health` preflight passed afterward. No live retry was
performed.

## Remaining Work

Run one controlled Claude minimal request through the repaired backend API.
Only if it passes should the Agent uses Claude request run once.

## Controlled Live Verification - 2026-06-15

- Single-owner workspace: **PASS**
- Backend owner PID was recorded while the workspace was active.
- `workspace_reused=true`
- `second_context_created=false`
- Claude minimal prompt count: **1**
- Claude minimal result: **FAIL**
- Agent uses Claude live: **SKIPPED**
- Total live prompts: **1**
- Other providers called: **none**
- Evidence: `runtime/evidence/web_ai/claude/20260615_000310`

The prompt was sent successfully through the backend-owned workspace. Claude
displayed `This model isn't available right now`, so no reliable assistant
answer existed. Extraction rejected the page and returned `body_fallback`
PARTIAL instead of treating sidebar/page text as a PASS. No retry was made.

After the run, the backend exited normally, the owner file was removed, and
port `8422` had no listener.

## Controlled Live Verification - 2026-06-15 (Model Available Follow-up)

- Claude minimal live: **FAIL before send**
- Agent uses Claude live: **SKIPPED**
- Backend workspace reused: `true`
- Second context created: `false`
- Controlled Claude ask attempts: `1`
- Actual prompts sent to Claude: `0`
- `send_success=false`
- `extract_success=false`
- `answer_quality`: not run
- `evidence_saved=false`
- Failure reason: `stale_conversation`
- Workspace state after the attempt: `STALE_CONVERSATION`
- Workspace URL: `https://claude.ai/new`
- Other providers called: **none**

The backend-owned workspace correctly prevented a send while the page was
classified as stale. Per the controlled-validation rule, no retry was made and
the Agent uses Claude live step was skipped.

## Valid Answer With Page Warning - 2026-06-15

- Claude minimal live: **PASS_WITH_WARNING**
- Agent uses Claude live: **PASS**
- Total live prompts: `2`
- `workspace_reused=true`
- `second_context_created=false`
- Answer selector: `[class*='font-claude']`
- Warning class: `non_blocking_warning`
- Warning text: `Claude Fable 5 is currently unavailable.`
- Minimal evidence: `runtime/evidence/web_ai/claude/20260615_013734`
- Agent evidence: `runtime/evidence/web_ai/claude/20260615_013814`

Reliable assistant answers now take priority over unrelated page warnings.
Warnings remain recorded separately and body/sidebar fallback cannot pass.

## Real Project Completion Sprint Boundary - 2026-06-15

The following real-project completion sprint made zero Claude calls and did not
open or modify provider workspaces. External AI remains an explicitly bounded,
optional escalation path; all four completion-matrix cases passed locally.

## Final Product Joint Task - 2026-06-15

- One Claude live call was made for a real copied-project diagnosis.
- `workspace_reused=true`
- `second_context_created=false`
- Send/extract/evidence: PASS
- Answer quality: `PASS_WITH_WARNING`
- No other provider was called.
- The local Agent applied the diagnostic conclusion safely and revalidated the
  project copy.
