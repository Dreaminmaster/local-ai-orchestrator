# Provider Login And Test Plan

Date: 2026-06-20

## Current Runtime Status

Final App under test:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/final-provider-login-smoke/Applications/Local AI Orchestrator.app`

Final DMG:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-unsigned.dmg`

Observed from packaged `/api/health` and `/api/providers`:

| Provider | Type | Current state | Route eligible | Notes |
| --- | --- | --- | --- | --- |
| LM Studio | Local model | READY / VERIFIED | yes | endpoint `http://127.0.0.1:1234`, default model `qwen2.5-coder-14b-instruct-mlx` |
| Ollama | Local model | DISABLED / skipped by user | no | user chose not to use |
| Claude | Web AI | NEED_LOGIN | no | project workspace supported |
| ChatGPT | Web AI | NEED_LOGIN | no | project workspace supported |
| Gemini | Web AI | NEED_LOGIN | no | project workspace supported |
| Kimi | Web AI | NEED_LOGIN | no | project workspace supported |
| Doubao | Web AI | NEED_LOGIN | no | project workspace supported |

## Login And Test Order

1. Claude
2. ChatGPT
3. Gemini
4. Kimi
5. Doubao

If a provider blocks on captcha, account restriction, region restriction, phone requirement, model unavailability, or page change, record the real state and continue to the next provider. Do not retry indefinitely.

## User Actions Required Per Provider

For each provider, the user should use the packaged App UI:

1. Open the **AI 服务** page.
2. Find the provider card.
3. Click **打开工作区**.
4. Complete login in the project-specific Chromium window.
5. Complete captcha, email/phone/security confirmation, or model selection manually if required.
6. Do not close the provider workspace window after login.
7. Return to the App and click **我已登录，检测并测试**.
8. Reply in Codex: `<Provider> 已登录` or `<Provider> 登录受限：<reason>`.

The App must use project-specific profiles under App Data and must not read daily Chrome/Safari profiles.

## Minimal Prompt

Every web provider minimal test uses exactly:

`请只回复：连接正常`

Limits:

- Maximum one minimal prompt per provider.
- If the prompt is not actually sent, it does not count.
- If sending succeeds but the page returns an error, record the error and do not automatically retry.
- Evidence may store redacted prompt, extracted answer, screenshot, and metadata.
- Evidence must not store cookies, tokens, passwords, or browser profile data.

## Agent Joint Task Scope

Required:

- LM Studio local-only Agent task: PASS expected.
- Claude Agent joint task: PASS or USER_PENDING.
- ChatGPT Agent joint task: PASS or USER_PENDING.

Optional:

- Gemini, Kimi, Doubao Agent joint task only if minimal passes and the UI/API path is already stable.

Agent prompt:

`这里有一个 Python TypeError 摘要，请给出一句简短修复建议。本地 Agent 根据建议修复隔离项目并生成中文报告。`

Limits:

- Maximum one Agent prompt per Provider.
- Do not send private project source.
- Do not call other unverified Providers.

## Routing Tests

Run four routing checks after provider status is known:

1. Fully local: LM Studio only, `external_ai_calls=0`.
2. Local-first: local attempts first; external AI only if needed and only from verified providers.
3. Manual confirmation: denial prevents web AI call; approval allows one verified provider call.
4. Best capability: choose among verified providers by priority; never choose NEED_LOGIN, skipped, disabled, or unverified providers.

Record:

- routing decision
- selected provider
- reason
- prompt count
- fallback used
- final status

## Status Classification

Use one of:

- VERIFIED
- VERIFIED_WITH_WARNING
- NEED_LOGIN
- CAPTCHA_REQUIRED
- ACCOUNT_RESTRICTED
- REGION_RESTRICTED
- MODEL_UNAVAILABLE
- PROVIDER_CHANGED
- FAILED_PRODUCT_BUG
- SKIPPED_BY_USER

External restrictions that do not count as product bugs:

- captcha or human verification
- account security checks
- subscription/model access limits
- phone or identity requirement
- region/service availability limits
- provider-side outage

Product bugs:

- App cannot open a provider workspace.
- App opens daily Chrome/Safari instead of project profile.
- Logged-in provider cannot be detected.
- Minimal prompt cannot be sent because of local code/selector failure.
- Extractor passes body/sidebar fallback as success.
- Evidence leaks credentials, cookies, tokens, or profile data.
- Unverified provider participates in automatic routing.
- Settings do not persist after App restart.

## Prompt Budget

Maximum live prompts for this provider acceptance pass:

- Web minimal: 5 total, one per provider.
- Agent joint tasks: 2 required max, Claude and ChatGPT only unless explicitly useful and stable.
- Total intended maximum: 7 web prompts.

No infinite retries. No cross-provider fallback during provider tests.

## Single-Owner Browser Rules

- Reuse backend-owned workspace.
- Do not create a second browser context for the same provider.
- Use project-specific persistent profile only.
- `workspace_reused=true` is expected after initial open.
- `second_context_created=false` is required.

## Reports To Produce

- `PROVIDER_FULL_LOGIN_ACCEPTANCE_REPORT.md`
- `WEB_PROVIDER_REAL_LOGIN_MATRIX_REPORT.md`
- `FINAL_REAL_MACHINE_FULL_ACCEPTANCE_REPORT.md`

These reports must distinguish automatic checks, packaged UI checks, API checks, and user-assisted login steps.
