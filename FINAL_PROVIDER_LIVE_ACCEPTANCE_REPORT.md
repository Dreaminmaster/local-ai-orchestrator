# Final Provider Live Acceptance Report

Date: 2026-06-16

## Overall

`PARTIAL / USER_PENDING`

This is an optional third-party account state, not a product implementation
failure. Final product delivery status is
`PASS_WITH_USER_PENDING_PROVIDER_LOGINS`.

| Provider | Product state | Live acceptance | Reason |
| --- | --- | --- | --- |
| LM Studio | READY / VERIFIED | PASS | Minimal chat and all five roles passed with `qwen2.5-coder-14b-instruct-mlx`. |
| Ollama | Disabled by user | SKIPPED_BY_USER | It is shown as not enabled and does not participate in routing. |
| Claude | NEED_USER_INTERVENTION | NOT_SENT | Project workspace opened, but the page required user action before the minimal prompt. |
| ChatGPT | NEED_LOGIN | NOT_SENT | Project workspace opened and requires login. |
| Gemini | NEED_LOGIN | NOT_SENT | Project workspace opened but login/readiness was not verified. |
| Kimi | NEED_LOGIN | NOT_SENT | Project workspace opened but login/readiness was not verified. |
| Doubao | NEED_LOGIN | NOT_SENT | Project workspace opened but login/readiness was not verified. |

## Live Call Counts

- LM Studio: 6 real calls: one minimal and five role checks.
- Web AI: 0 prompts sent in this sprint.
- No cross-provider fallback occurred.

The web result is an expected user-login boundary, not a provider adapter crash.
All five project-specific workspace windows were created by the same backend
owner and exposed through the unified App workflow.

Every unverified web Provider reports `route_eligible=false`; none is called by
automatic routing before the user completes in-App login and verification.
