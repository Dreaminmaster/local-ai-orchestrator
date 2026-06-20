# Provider Full Login Acceptance Report

Checked at: 2026-06-20 23:24 Asia/Shanghai

## Result

Provider short-answer regression: PASS for Claude and Kimi.

Full all-provider login acceptance: PARTIAL.

Reason: this sprint fixed and verified the known short-answer bugs for Claude and Kimi. ChatGPT, Gemini, and Doubao were intentionally not live-tested in this round.

## Local Providers

| Provider | Status | Result |
| --- | --- | --- |
| LM Studio | VERIFIED | PASS. Endpoint reachable and available as the default local model provider. |
| Ollama | SKIPPED_BY_USER | PASS. Disabled and excluded from routing. |

## Web Providers

| Provider | Login/workspace | Minimal | Agent route eligibility |
| --- | --- | --- | --- |
| Claude | READY | PASS_WITH_WARNING | Eligible after provider report refresh; current console quality is pass with warning. |
| Kimi | READY | PASS | Eligible after provider report refresh; current console quality is pass. |
| ChatGPT | USER_PENDING | Not run | Not eligible |
| Gemini | USER_PENDING | Not run | Not eligible |
| Doubao | USER_PENDING | Not run | Not eligible |

## Fixes Verified

- Claude short answer `连接正常` no longer fails as body fallback.
- Kimi short answer `连接正常` no longer fails as body fallback.
- Body fallback containing `连接正常` still fails in offline tests.
- Old short messages outside the latest-message window do not pass.
- Reliable selectors can accept short minimal answers.
- Non-blocking model warning banners are no longer treated as blocking when a valid answer exists.

