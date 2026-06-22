# Provider Workspace Console Report

Checked at: 2026-06-20 23:24 Asia/Shanghai

## Result

Provider Workspace Console: PASS

Implemented approach: controlled external Chromium windows plus an in-App console.

True embedded third-party webpages were not implemented in this sprint. The current approach avoids fragile iframe/WebView embedding against third-party pages that may use CSP, X-Frame, account security checks, and provider-specific anti-automation behavior. The App now presents a unified console while the backend owns and manages one persistent Playwright workspace per provider.

## What Changed

- Added `/api/web-ai/workspaces/console`.
- Added backend exchange tracking for latest prompt, answer, quality result, selector, warning, evidence path, task id, and step id.
- Added AI 服务 page section: `AI 工作区控制台`.
- Console shows Claude, ChatGPT, Gemini, Kimi, and Doubao together.
- Console actions include open/focus workspace, recheck, test connection, and close workspace.
- Open behavior remains single-owner: if a workspace exists, it is brought to front instead of creating a second context.

## Live Console State After Fix

| Provider | Workspace state | Last prompt | Last answer | Quality | Selector | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Claude | READY | `请只回复：连接正常` | `连接正常` | PASS_WITH_WARNING | `[class*='font-claude']` | `runtime/evidence/web_ai/claude/20260620_232300` |
| Kimi | READY | `请只回复：连接正常` | `连接正常` | PASS | `.markdown` | `runtime/evidence/web_ai/kimi/20260620_232342` |
| ChatGPT | CLOSED | — | — | — | — | — |
| Gemini | CLOSED | — | — | — | — | — |
| Doubao | CLOSED | — | — | — | — | — |

## E2E

Script: `scripts/e2e_provider_workspace_console.py`

Result: PASS

Covered:

- Console lists all main web providers.
- Each provider exposes state and project profile path.
- Console summary counts are present.
- Claude and Kimi show latest prompt / answer / evidence after live minimal.

Not covered:

- True embedded provider page rendering inside Tauri WebView.
- Direct packaged WebView click automation after this source-only fix.

## Window Management

Current behavior:

- One backend-owned browser context per provider.
- Open requests are guarded on frontend and backend.
- Reopening an existing workspace brings it to front.
- `workspace_reused=true` and `second_context_created=false` were confirmed for Claude and Kimi live minimal.

Next improvement:

- Add OS-level window positioning/focus hints per provider for a more docked feel.

## Workspace Reuse Semantics Update - 2026-06-21

- Repeated open now separates `request_id` from stable `workspace_id`.
- Existing workspaces return `workspace_already_open=true`, `workspace_reused=true`, `same_window_focused=true`, `new_context_created=false`, and `second_context_created=false`.
- Provider Console shows workspace id, opened/focused timestamps, reuse state, and context creation state.
- Claude and Kimi repeated-open behavior is covered by offline unit tests.
- No live provider prompt was sent for this update.

## Packaged App Rebuild Verification - 2026-06-20

The Provider Workspace Console has been rebuilt into the arm64 unsigned DMG:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-provider-console-unsigned.dmg`

Packaged smoke result:

- `/api/web-ai/workspaces/console`: PASS.
- `scripts/e2e_provider_workspace_console.py`: PASS against the packaged sidecar.
- Console provider rows: Claude, ChatGPT, Gemini, Kimi, Doubao.
- Profile paths: App Data project-specific browser profiles.
- Live prompts during this packaged smoke: `0`.
