# External AI Live Workflow Report

Updated: 2026-06-12

## Result

**External AI Live Workflow Sprint: PARTIAL**

The Claude user-intervention workflow is ready and its offline pending/resume checks pass. Project-specific Playwright Chromium is now installed. The controlled live attempt stopped before sending because the standalone E2E process tried to open a persistent profile already owned by the backend workspace process.

## Safety

- Only Claude Web was considered.
- ChatGPT, Doubao, Kimi, and Gemini were not tested.
- No provider profile was reset.
- No daily Chrome or Safari profile was read.
- No Playwright browser was downloaded.
- No cookies, profiles, or raw evidence are intended for source control.

## Pending And Resume

Report: `runtime/test_reports/e2e_external_ai_live_workflow.json`

| Check | Result |
| --- | --- |
| Claude unlogged state saves pending action | PASS |
| Claude READY mock | PASS |
| Resume while still unready does not send | PASS |
| Resume READY mock executes pending action | PASS |
| Task history records needs-user product state | PASS |

Profile-directory existence is no longer treated as proof of login. Claude becomes READY only after an active project workspace page is inspected and its composer is visible.

## Project-Specific Playwright Chromium

- Installed: **PASS**
- Path: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.playwright-browsers/chromium-1223`
- API status: `chromium_found=true`
- System/default Playwright cache used: **no**
- Other browser profiles modified: **no**

## Claude Workspace And Live Attempt

- Claude workspace: **READY**
- Claude workspace URL: `https://claude.ai/new`
- Minimal Claude live task: **FAIL before send**
- Agent uses Claude Web live task: **SKIPPED**
- Actual live Claude prompts sent: **0**
- `send_success=false`
- `extract_success=false`
- Evidence saved: `runtime/evidence/web_ai/claude/20260612_204757`
- Failure reason: persistent profile already open in the backend workspace; the standalone E2E process could not acquire the same profile.

No retry was performed. No ChatGPT or other provider fallback was attempted.

## UI Status

Browser UI verification passed:

- Claude Web: `NEED_LOGIN`, with “Claude 未登录，点击打开工作区。”
- ChatGPT Web: `NOT_CONFIGURED`, shown as an untested fallback
- Doubao, Kimi, Gemini: grouped under “未启用 provider”
- Pending task: visible as paused / needs user
- Recent tasks: name, status, timestamps, tool count, evidence count, report, task directory, and resume action
- Project browser missing prompt: visible and non-blocking for local tasks

## Recommendation

The next implementation step is to make live E2E call the backend-owned reusable workspace, or explicitly close that workspace before launching a standalone process. Do not retry live until that ownership path is chosen.

## Single-Owner Architecture Follow-up - 2026-06-12

- Backend `WorkspaceManager` is now the only persistent-profile owner.
- Claude asks use `POST /api/external-ai/workspaces/claude/ask`.
- Provider requests are serialized with a backend lock.
- Owner diagnostics use `.workspace-owner.json` without sensitive data.
- Claude initialization, provider test, workspace E2E, and live workflow scripts
  no longer open a second persistent context.
- Single-owner focused tests: 10/10 PASS.
- Relevant offline tests: 31/31 PASS.
- Controlled live workflow stopped in backend API preflight before prompt send.
- Preflight root cause: local `urllib` proxy handling; fixed and verified with a
  non-live `/api/health` backend startup check.
- No live retry was performed.
- Claude minimal live: SKIPPED; Agent uses Claude live: SKIPPED.
- Actual live Claude prompts: 0; other providers called: none.

## Backend-Owned Live Verification - 2026-06-15

- Claude minimal live: **FAIL**
- Agent uses Claude live: **SKIPPED**, because minimal did not PASS
- Profile owner: `backend`
- Workspace reused: `true`
- Second context created: `false`
- Prompt sent successfully: `true`
- Live prompt total: `1`
- Evidence saved: `runtime/evidence/web_ai/claude/20260615_000310`
- Other providers called: none

Claude returned a page-level model availability message:
`This model isn't available right now`. No reliable assistant message was
available, and the extractor correctly limited the result to PARTIAL
`body_fallback`. No live retry was performed.

## Backend-Owned Controlled Follow-up - 2026-06-15

- Claude minimal live: **FAIL before send**
- Agent uses Claude live: **SKIPPED**
- `workspace_reused=true`
- `second_context_created=false`
- Actual Claude prompts sent: `0`
- `send_success=false`
- `extract_success=false`
- `answer_quality`: not run
- `evidence_saved=false`
- Failure reason: `stale_conversation`
- Workspace state: `STALE_CONVERSATION`
- Other providers called: none

The single-owner backend API was used. It detected a stale Claude conversation
before sending and returned `need_user_intervention=true`. No retry or provider
fallback was attempted.

## Warning-Aware Live Verification - 2026-06-15

- Minimal: **PASS_WITH_WARNING**
- Agent uses Claude: **PASS**
- Actual live prompts: `2`
- Reliable answer selector: `[class*='font-claude']`
- Warning class: `non_blocking_warning`
- Warning did not contaminate extracted answer text.
- Evidence records prompt/answer timestamps, answer selector, warning text,
  warning class, and quality result.
- No other provider was called.
