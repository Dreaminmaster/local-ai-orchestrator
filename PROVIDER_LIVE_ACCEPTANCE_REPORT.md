# Provider Live Acceptance Report

Checked at: 2026-06-16

## Current Acceptance

| Provider | State | Acceptance | Live calls |
| --- | --- | --- | ---: |
| LM Studio | READY | VERIFIED | 6 |
| Ollama | NEED_LOCAL_SERVICE | SKIPPED_BY_USER | 0 |
| Claude Web | NEED_LOGIN | NOT_RUN | 0 |
| ChatGPT Web | DISABLED | NOT_RUN | 0 |
| Gemini Web | DISABLED | NOT_RUN | 0 |
| Kimi Web | DISABLED | NOT_RUN | 0 |
| Doubao Web | DISABLED | NOT_RUN | 0 |

LM Studio live calls comprise one minimal chat and five role-specific checks.
No external web AI provider was called.

## Packaged App Preflight

- Backend health: PASS
- Runtime mode: installed/custom app-data mode
- App data root: `~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator`
- LM Studio reachable: true
- Ollama reachable: false
- Project Playwright browser path is configured under app data.

## Next User-Gated Steps

1. Ollama was explicitly skipped by the user and does not block acceptance.
2. For Claude Web acceptance, open the project-specific Claude workspace and
   complete manual login before any live prompt is sent.
