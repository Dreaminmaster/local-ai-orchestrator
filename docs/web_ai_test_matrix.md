# External AI Web Test Matrix

Test outputs should be written to:

```text
runtime/test_reports/web_ai/
```

| Provider | Script | Persistent profile | Login detection | Send prompt | Wait complete | Extract answer | Follow-up | Evidence saved | Desktop fallback |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ChatGPT | `scripts/test_web_ai_chatgpt.py` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Claude | `scripts/test_web_ai_claude.py` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Doubao | `scripts/test_web_ai_doubao.py` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Gemini | `scripts/test_web_ai_gemini.py` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Kimi | `scripts/test_web_ai_kimi.py` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## How to run

1. Start the project environment.
2. Ensure Playwright browsers are installed.
3. Run each provider once with `headless=False` and log in manually.
4. Re-run the test and confirm profile reuse.

Example:

```bash
PYTHONPATH=. python scripts/test_web_ai_chatgpt.py
```

Each script should save a JSON test report under `runtime/test_reports/web_ai/`.
