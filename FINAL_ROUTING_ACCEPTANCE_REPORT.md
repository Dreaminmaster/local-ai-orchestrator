# Final Routing Acceptance Report

Date: 2026-06-16

## Result

`PARTIAL`

## Routing Rules Verified

- Fully local: selects LM Studio and does not call web AI.
- Local first: selects ready LM Studio.
- Disabled Ollama does not participate.
- Enabled but unverified web providers do not participate.
- Web priority is configurable in the App with up/down controls.
- Call limit and manual-confirmation behavior are covered by regression tests.

## Real Tasks

| Scenario | Result | External calls | Notes |
| --- | --- | ---: | --- |
| Fully local packaged task | PASS | 0 | Packaged sidecar completed a real-project task and wrote `final_report.md`. |
| Local first | PASS | 0 | LM Studio was selected; no verified web provider was eligible. |
| Manual confirmation | PARTIAL | 0 | Confirmation and refusal semantics pass offline tests, but an allowed real web call could not run before a provider login was completed. |

The product correctly prefers no web call over routing to an unverified
provider.

The Agent repair matrix completed 10/10 with bounded local-model reporting
fallback.
