# External AI Web Test Matrix

Generated from real JSON reports under:

```text
runtime/test_reports/web_ai/
```

Last generated: 2026-06-01T02:05:49.416320

| Provider | Script | Login | Send | Wait | Extract | Follow-up | Evidence | Fallback | AQ | Status | Last Tested |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|

| Chatgpt | `scripts/test_web_ai_chatgpt.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | NOT_RUN | not_run | — |
| Claude | `scripts/test_web_ai_claude.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | NOT_RUN | not_run | — |
| Doubao | `scripts/test_web_ai_doubao.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | NOT_RUN | not_run | — |
| Gemini | `scripts/test_web_ai_gemini.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | NOT_RUN | not_run | — |
| Kimi | `scripts/test_web_ai_kimi.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | NOT_RUN | not_run | — |

## Report schema

Each provider test writes:

```json
{
  "provider": "chatgpt",
  "success": false,
  "login_detection": true,
  "send_prompt": true,
  "wait_complete": false,
  "extract_answer": false,
  "follow_up": false,
  "evidence_saved": true,
  "answer_quality": {"quality": "PARTIAL", "issues": ["empty_or_short"], "reliable": false},
  "fallback_result": "desktop_visual",
  "raw": {},
  "created_at": "..."
}
```

AQ = Answer Quality. Low-quality answers (login page, captcha, rate limit,
network error, empty) are flagged PARTIAL/FAIL even if technically extracted.

## How to run

1. Start project environment.
2. Ensure Playwright browsers are installed.
3. Manually log in once per provider to establish persistent profiles.
4. Run each script:

```bash
PYTHONPATH=. python scripts/test_web_ai_chatgpt.py
```
