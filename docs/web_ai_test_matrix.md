# External AI Web Test Matrix

Generated from real JSON reports under:

```text
runtime/test_reports/web_ai/
```

Last generated: 2026-06-02T02:52:37.546845

| Provider | Script | Login | Send | Wait | Extract | Follow-up | Evidence | Evidence Path | Used Selector | Failure Stage | Fallback | AQ | Status | Last Tested |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---|

| Chatgpt | `scripts/test_web_ai_chatgpt.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `runtime/evidence/web_ai/chatgpt/20260601_232216` | `body_fallback` | answer_quality | — | PARTIAL | failed | 2026-06-01T23:22:16 |
| Claude | `scripts/test_web_ai_claude.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `runtime/evidence/web_ai/claude/20260601_232239` | `body_marker:claude` | — | — | PASS | success | 2026-06-01T23:23:00 |
| Doubao | `scripts/test_web_ai_doubao.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | `—` | `—` | — | — | NOT_RUN | not_run | — |
| Gemini | `scripts/test_web_ai_gemini.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | `—` | `—` | — | — | NOT_RUN | not_run | — |
| Kimi | `scripts/test_web_ai_kimi.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | `—` | `—` | — | — | NOT_RUN | not_run | — |

## Agent E2E

| Scenario | Script | Selected Target | Used Selector | AQ | Evidence | Evidence Path | Report Contains Claude Web | Status | Last Tested |
|---|---|---|---|---:|---:|---|---:|---:|---|
| Claude Web escalation | `scripts/e2e_agent_uses_claude_web.py` | Claude Web | `body_marker:claude` | PASS | ✅ | `runtime/evidence/web_ai/claude/20260602_025237` | ✅ | PASS | 2026-06-02T02:52:37 |

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
  "evidence_path": "runtime/evidence/web_ai/chatgpt/...",
  "used_selector": "[data-message-author-role='assistant']",
  "failure_stage": "selector/send",
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
