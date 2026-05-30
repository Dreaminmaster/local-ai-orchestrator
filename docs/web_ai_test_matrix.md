# External AI Web Test Matrix

Generated from real JSON reports under:

```text
runtime/test_reports/web_ai/
```

Last generated: 2026-05-31T04:56:51.300538

| Provider | Script | Login | Send | Wait | Extract | Follow-up | Evidence | Fallback | Status | Last Tested |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| Chatgpt | `scripts/test_web_ai_chatgpt.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | not_run | — |
| Claude | `scripts/test_web_ai_claude.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | not_run | — |
| Doubao | `scripts/test_web_ai_doubao.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | not_run | — |
| Gemini | `scripts/test_web_ai_gemini.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | not_run | — |
| Kimi | `scripts/test_web_ai_kimi.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | not_run | — |

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
  "fallback_result": "desktop_visual",
  "raw": {},
  "created_at": "..."
}
```
