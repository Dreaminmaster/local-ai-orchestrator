# Final Real Machine Full Acceptance Report

Checked at: 2026-06-20 23:24 Asia/Shanghai

## Result

Real-machine regression sprint: PARTIAL

The two known failure classes were addressed:

1. Web Provider short-answer extraction: fixed and live-verified for Claude and Kimi.
2. Real repair verification strength: fixed so `compileall` PASS plus runtime FAIL no longer becomes success.

This sprint did not rebuild the DMG, so the currently installed final DMG is not updated with these fixes yet.

## Web Provider Regression

| Provider | Result | Details |
| --- | --- | --- |
| Claude | PASS_WITH_WARNING | Reliable selector `[class*='font-claude']`; answer `连接正常`; non-blocking warning `Claude Fable 5 is currently unavailable`. |
| Kimi | PASS | Reliable selector `.markdown`; answer `连接正常`. |

Live prompts used this sprint:

- Claude: 1
- Kimi: 1
- Other providers: 0

## Repair Verification Regression

| Case | Result |
| --- | --- |
| `compileall` PASS but `python3 main.py` raises `ModuleNotFoundError` | PASS: task now returns FAILED |
| Healthy `main.py` | PASS: task returns PASS |

Verification report:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/apple-silicon-rebuild/real-repair-verification-after-fix.json`

## Provider Workspace Console

Result: PASS

The App now has an AI 工作区控制台 backed by `/api/web-ai/workspaces/console`.

It uses controlled external Chromium workspaces rather than embedded third-party iframes. This is the safer current design because provider pages may block embedding through CSP, X-Frame, account security flows, or provider-specific page changes.

## Checks

- `node --check frontend/app.js`: PASS
- `scripts/health_check.py`: PASS
- `scripts/beta_validation.py`: PASS, live skipped
- 34 focused unit tests: PASS
- `scripts/e2e_provider_workspace_console.py`: PASS

## Remaining Before Rebuild DMG

- Rebuild and smoke-test a new unsigned arm64 DMG with these source fixes.
- Optionally refresh provider test report files through the UI after rebuild.
- Continue live acceptance for ChatGPT, Gemini, and Doubao only when requested.

