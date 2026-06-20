#!/usr/bin/env python3
"""Legacy Claude workspace live E2E through the backend single-owner API."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_claude_workspace_live.json"
API_BASE = "http://127.0.0.1:8422/api"


def request(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=240) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    opened = request("/web-ai/workspace/claude/open", {})
    if opened.get("state") != "READY":
        output = {
            "created_at": datetime.now().isoformat(),
            "final_status": "NEED_USER_INTERVENTION",
            "provider": "Claude Web",
            "workspace_opened": True,
            "reused_existing_page": bool(opened.get("workspace_reused")),
            "profile_owner": opened.get("owner_type", "backend"),
            "second_context_created": False,
            "workspace_status_before_send": opened,
            "need_user_intervention": True,
            "failure_reason": f"claude_workspace_not_ready:{opened.get('state')}",
        }
    else:
        result = request(
            "/external-ai/workspaces/claude/ask",
            {
                "task_id": "e2e_claude_workspace_live",
                "prompt": "请用一句话说明如何安全复用项目专用 Claude 工作区。",
                "purpose": "workspace_live_e2e",
                "debug": True,
            },
        )
        quality = result.get("answer_quality") or {}
        output = {
            "created_at": datetime.now().isoformat(),
            "final_status": "PASS"
            if result.get("success") and quality.get("quality") == "PASS"
            else "NEED_USER_INTERVENTION"
            if result.get("need_user_intervention")
            else "FAIL",
            "provider": "Claude Web",
            "workspace_opened": True,
            "reused_existing_page": bool(result.get("workspace_reused")),
            "profile_owner": result.get("profile_owner", ""),
            "second_context_created": bool(result.get("second_context_created")),
            "workspace_status_before_send": opened,
            "answer_quality": quality.get("quality", "FAIL"),
            "quality_issues": result.get("quality_issues", []),
            "evidence_saved": bool(result.get("evidence_saved")),
            "evidence_path": result.get("evidence_path", ""),
            "need_user_intervention": bool(result.get("need_user_intervention")),
            "failure_reason": result.get("failure_reason", ""),
        }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["final_status"] in {"PASS", "NEED_USER_INTERVENTION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
