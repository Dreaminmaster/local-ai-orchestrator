#!/usr/bin/env python3
"""Update docs/web_ai_test_matrix.md from runtime/test_reports/web_ai/*.json."""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "runtime/test_reports/web_ai"
DOC = ROOT / "docs/web_ai_test_matrix.md"
PROVIDERS = ["chatgpt", "claude", "doubao", "gemini", "kimi"]


def mark(value):
    return "✅" if value else "❌"


def quality_mark(data):
    """Answer quality: PASS / PARTIAL / FAIL / NOT_RUN."""
    qc = data.get("answer_quality", {})
    if qc:
        return qc.get("quality", "PARTIAL")
    if data.get("status") == "not_run":
        return "NOT_RUN"
    return "—"


def load(provider):
    p = REPORT_DIR / f"{provider}.json"
    if not p.exists():
        return {"provider": provider, "status": "not_run"}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data | {
        "status": "success" if data.get("success") else "failed",
    }


def main():
    rows = []
    for provider in PROVIDERS:
        r = load(provider)
        row = (
            "| {provider} | `{script}` | {login} | {send} | {wait} | {extract}"
            " | {follow} | {evidence} | {fallback} | {quality} | {status} | {tested} |"
        ).format(
            provider=provider.title(),
            script=f"scripts/test_web_ai_{provider}.py",
            login=mark(r.get("login_detection")),
            send=mark(r.get("send_prompt")),
            wait=mark(r.get("wait_complete")),
            extract=mark(r.get("extract_answer")),
            follow=mark(r.get("follow_up")),
            evidence=mark(r.get("evidence_saved")),
            fallback=r.get("fallback_result") or "—",
            quality=quality_mark(r),
            status=r.get("status", "not_run"),
            tested=r.get("created_at", "—")[:19],
        )
        rows.append(row)

    content = ("""# External AI Web Test Matrix

Generated from real JSON reports under:

```text
runtime/test_reports/web_ai/
```

Last generated: {now}

| Provider | Script | Login | Send | Wait | Extract | Follow-up | Evidence | Fallback | AQ | Status | Last Tested |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|

{rows}

## Report schema

Each provider test writes:

```json
{{
  "provider": "chatgpt",
  "success": false,
  "login_detection": true,
  "send_prompt": true,
  "wait_complete": false,
  "extract_answer": false,
  "follow_up": false,
  "evidence_saved": true,
  "answer_quality": {{"quality": "PARTIAL", "issues": ["empty_or_short"], "reliable": false}},
  "fallback_result": "desktop_visual",
  "raw": {{}},
  "created_at": "..."
}}
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
""").format(now=datetime.now().isoformat(), rows="\n".join(rows))

    DOC.write_text(content, encoding="utf-8")
    print(DOC)


if __name__ == "__main__":
    main()
