# External AI Workspace

The External AI Web Workspace allows the local orchestrator to ask stronger AI systems through logged-in web sessions.

## Implemented alpha capabilities

- Persistent Playwright profiles via `BrowserProfileManager`
- Independent profiles:
  - `chatgpt`
  - `claude`
  - `doubao`
  - `gemini`
  - `kimi`
- Login detection
- Input-box locating
- Send prompt
- Wait for answer stability
- Extract latest answer
- Multi-turn follow-up when answer is too vague
- Save Q/A evidence to `runtime/evidence/web_ai/`
- Screenshot evidence
- Selector/page failure fallback to `desktop_visual`

## Files

```text
backend/browser/profile_manager.py
backend/skills/external_ai_web/
```

## Production hardening still needed

- Real selector tuning against live ChatGPT / Claude / Gemini / Kimi / Doubao pages
- Login recovery UI
- Captcha/manual-intervention handling
- Provider-specific answer completion signals
