# Unified Provider Onboarding Report

Date: 2026-06-16

## Result

`PASS`

The AI Services page now provides one product-owned onboarding flow for all
supported providers. Users no longer need Codex to edit `settings.json`.

## Delivered

- One "选择要使用的 AI 服务" flow covers LM Studio, Ollama, Claude, ChatGPT,
  Gemini, Kimi, and Doubao.
- Each provider can be set to enabled, temporarily skipped, or configure later.
- Current user choices are persisted:
  - LM Studio: enabled
  - Ollama: skipped / disabled
  - Claude, ChatGPT, Gemini, Kimi, Doubao: enabled for configuration
- The wizard processes LM Studio, Claude, ChatGPT, Gemini, Kimi, and Doubao in
  one sequence.
- Web steps provide open workspace, recheck, and "我已登录，检测并测试".
- Live minimal requires an explicit App action and is limited to one persisted
  onboarding result per provider.
- Failed or externally blocked web providers do not block the remaining wizard.
- The task page now shows only current local provider, current external
  provider, and routing mode.

## Safety

- Project-specific persistent profiles only.
- No daily Chrome or Safari profile access.
- No password, cookie, token, or profile data is written to reports.
- Unverified providers cannot participate in automatic routing.

