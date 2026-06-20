# Web AI Provider Matrix Report

## Shared Architecture

Claude, ChatGPT, Gemini, Kimi, and Doubao use project/App-data Playwright profiles, one backend-owned persistent context per Provider, Provider locks, manual login, shared evidence, and shared answer-quality rules.

| Provider | Workspace Product Controls | Shared Adapter Contract | Current Runtime State | Live This Sprint |
|---|---|---|---|---|
| Claude | Complete | Complete | NEED_LOGIN | No |
| ChatGPT | Complete | Complete | DISABLED / NOT_CONFIGURED | No |
| Gemini | Complete | Complete | DISABLED / NOT_CONFIGURED | No |
| Kimi | Complete | Complete | DISABLED / NOT_CONFIGURED | No |
| Doubao | Complete | Complete | DISABLED / NOT_CONFIGURED | No |

Body/sidebar fallback cannot produce a PASS. Live minimal tests remain explicit opt-in and limited to one prompt per Provider.
