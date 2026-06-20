# Local Model Live Acceptance Report

Checked at: 2026-06-16

## LM Studio

- Endpoint: `http://127.0.0.1:1234`
- Detection: PASS (`/v1/models` returned HTTP 200)
- State: `READY`
- Acceptance status: `VERIFIED`
- OpenAI-compatible API: true
- Selected model: `qwen2.5-coder-14b-instruct-mlx`
- Settings path: `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/settings.json`
- Minimal live chat: PASS
- Minimal response: `连接正常`
- Planner role: PASS
- Executor role: PASS
- Repair role: PASS
- Verifier role: PASS
- Summarizer role: PASS
- Local-only routing decision: `lmstudio`
- External AI calls during this acceptance: 0

## Ollama

- Endpoint: `http://127.0.0.1:11434`
- State: `NEED_LOCAL_SERVICE`
- Enabled: false
- Acceptance: `SKIPPED_BY_USER`
- User decision: temporarily not using Ollama
- No installation or automatic startup was attempted.

## Notes

- The packaged backend at `http://127.0.0.1:8422` was used for detection,
  configuration, minimal chat, role tests, and routing verification.
- The in-app browser client blocked localhost navigation, so the model setting
  was saved through the packaged product API rather than by browser automation.
- No web provider was called.
