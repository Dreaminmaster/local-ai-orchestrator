#!/usr/bin/env python3
"""Claude provider smoke through the backend-owned workspace API."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    payload = json.dumps(
        {
            "task_id": "test_web_ai_claude",
            "prompt": "请用一句话回答：local-ai-orchestrator 的目标是什么？",
            "purpose": "provider_test",
            "debug": args.debug,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:8422/api/external-ai/workspaces/claude/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.loads(response.read().decode("utf-8"))

    report = {
        "provider": "claude",
        "success": bool(result.get("success")),
        "login_detection": not bool(result.get("need_user_intervention")),
        "send_prompt": bool(result.get("send_success")),
        "wait_complete": bool(result.get("extract_success")),
        "extract_answer": bool(result.get("extract_success")),
        "answer_quality": result.get("answer_quality", {}),
        "evidence_saved": bool(result.get("evidence_saved")),
        "evidence_path": result.get("evidence_path", ""),
        "used_selector": result.get("used_selector", ""),
        "failure_stage": result.get("failure_reason", ""),
        "profile_owner": result.get("profile_owner", ""),
        "workspace_reused": bool(result.get("workspace_reused")),
        "second_context_created": bool(result.get("second_context_created")),
        "created_at": datetime.now().isoformat(),
    }
    out = Path("runtime/test_reports/web_ai/claude.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
