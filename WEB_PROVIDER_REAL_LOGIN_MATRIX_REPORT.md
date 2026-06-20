# Web Provider Real Login Matrix Report

Checked at: 2026-06-20 23:24 Asia/Shanghai

Minimal prompt: `请只回复：连接正常`

## Result

Web provider short-answer acceptance: PASS for Claude and Kimi.

| Provider | Workspace | Prompt sent this sprint | Answer | Quality | Selector | Evidence | Result |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| Claude | READY, backend-owned, project profile | 1 | `连接正常` | PASS_WITH_WARNING | `[class*='font-claude']` | `runtime/evidence/web_ai/claude/20260620_232300` | PASS_WITH_WARNING |
| Kimi | READY, backend-owned, project profile | 1 | `连接正常` | PASS | `.markdown` | `runtime/evidence/web_ai/kimi/20260620_232342` | PASS |
| ChatGPT | CLOSED / not tested this sprint | 0 | — | — | — | — | USER_PENDING |
| Gemini | CLOSED / not tested this sprint | 0 | — | — | — | — | USER_PENDING |
| Doubao | CLOSED / not tested this sprint | 0 | — | — | — | — | USER_PENDING |

## Safety

- No daily Chrome or Safari profile was used.
- No cookie, token, profile data, or credentials were copied into reports.
- Body/sidebar fallback remains disallowed for PASS.
- Claude warning banner was classified as non-blocking because a reliable new assistant message was extracted.
- Existing failed minimal reports no longer block future re-test; only successful minimal reports are reused.

## Remaining Provider Work

ChatGPT, Gemini, and Doubao still need their own live acceptance later. This sprint intentionally did not call them.

