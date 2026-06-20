# Provider Integration Final Sprint Report

## Result

**PARTIAL**

The packaged product now exposes a unified, user-configurable Provider experience. The remaining partial items require local services, accounts, regions, login, or explicit live-test permission.

## Product Capabilities Completed

- Unified settings and status model for LM Studio, Ollama, Claude, ChatGPT, Gemini, Kimi, and Doubao.
- AI Services page supports provider enable/disable, endpoint/model settings, local model roles, web workspace controls, routing policy, priority, diagnostics, and profile reset.
- Five web adapters use the backend-owned single-owner workspace path and shared send/extract/quality/evidence contracts.
- Routing excludes disabled, failed, and unconfigured providers.
- Project/App-data Playwright Chromium installation requires an explicit user click, supports cancel, and never silently downloads.
- Product capability matrix is generated from real reports and profile state.

## Current Provider State

| Provider | Current Result | Live This Sprint |
|---|---|---|
| LM Studio | DISCONNECTED; UI configuration and detection available | No |
| Ollama | DISABLED/DISCONNECTED; UI configuration and detection available | No |
| Claude Web | NEED_LOGIN in packaged app; prior product work exists | No |
| ChatGPT Web | DISABLED / not configured | No |
| Gemini Web | DISABLED / not configured | No |
| Kimi Web | DISABLED / not configured | No |
| Doubao Web | DISABLED / not configured | No |

No live web prompt was sent during this sprint.

## Validation

- Provider contract tests: 41/41 PASS
- Repair matrix: 10/10 PASS
- Health check: PASS
- Beta validation: PASS
- Browser product UI: PASS
- Packaged App Provider health/UI-ready/shutdown: PASS
- Final DMG install smoke: PASS
- Provider integration matrix: PARTIAL, with live disabled by default

## Honest Completion Boundary

Users can configure and manage all Providers from the packaged App. The product is not a full Provider PASS until local model services are running and the desired web Providers are manually logged in and explicitly live-tested.

## Unified Onboarding Follow-up - 2026-06-16

- LM Studio is now READY / VERIFIED with `qwen2.5-coder-14b-instruct-mlx`.
- Ollama is `SKIPPED_BY_USER`, not an error.
- All five web providers are enabled for configuration and visible in one
  onboarding wizard.
- Project-specific workspaces were opened and detected sequentially by one
  backend owner. No web prompt was sent because none reached a safe verified
  acceptance state.
- Latest packaged App build, bundled sidecar, health, UI-ready, local task, and
  shutdown smoke passed.
