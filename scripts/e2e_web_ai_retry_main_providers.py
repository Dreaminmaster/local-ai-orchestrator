#!/usr/bin/env python3
"""Retry Web AI tests for main providers only: ChatGPT and Claude."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/web_ai/main_providers_retry.json"
PROVIDERS = {
    "chatgpt": ROOT / "scripts/test_web_ai_chatgpt.py",
    "claude": ROOT / "scripts/test_web_ai_claude.py",
}


def load_report(provider: str) -> dict:
    path = ROOT / "runtime/test_reports/web_ai" / f"{provider}.json"
    if not path.exists():
        return {"provider": provider, "status": "not_run"}
    return json.loads(path.read_text(encoding="utf-8"))


def classify(data: dict) -> str:
    quality = (data.get("answer_quality") or {}).get("quality")
    if data.get("success") and quality == "PASS":
        return "PASS"
    if data.get("login_detection") and (
        data.get("send_prompt") or data.get("extract_answer") or data.get("evidence_saved")
    ):
        return "PARTIAL"
    return "FAIL"


def main() -> int:
    results = {}
    for provider, script in PROVIDERS.items():
        proc = subprocess.run(
            [sys.executable, str(script), "--debug"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=240,
        )
        data = load_report(provider)
        data["retry_returncode"] = proc.returncode
        data["retry_stdout_tail"] = proc.stdout[-4000:]
        data["retry_stderr_tail"] = proc.stderr[-4000:]
        data["retry_status"] = classify(data)
        results[provider] = data

    goals = {
        "chatgpt_at_least_partial": results["chatgpt"]["retry_status"]
        in ("PASS", "PARTIAL"),
        "claude_evidence_saved": bool(results["claude"].get("evidence_saved")),
        "claude_not_body_sidebar": (
            results["claude"].get("used_selector")
            and results["claude"].get("used_selector") != "body_fallback"
        ),
    }
    output = {
        "created_at": datetime.now().isoformat(),
        "results": results,
        "goals": goals,
        "pass": all(goals.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
