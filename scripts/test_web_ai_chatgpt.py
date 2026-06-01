#!/usr/bin/env python3
"""E2E smoke test for chatgpt Web AI adapter.
Requires Playwright browser and a logged-in persistent profile.
"""

import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from backend.skills.external_ai_web.web_ai_skill import WebAISkill
from backend.skills.external_ai_web.answer_quality_check import AnswerQualityChecker


def answer_quality(data: dict) -> dict:
    meta_quality = data.get("metadata", {}).get("quality_check")
    if meta_quality:
        return {
            "quality": meta_quality.get("quality", "PARTIAL"),
            "issues": [meta_quality.get("reason", "")] if meta_quality.get("reason") else [],
            "reliable": bool(meta_quality.get("passed")),
        }
    return AnswerQualityChecker().check(data.get("result") or "")


def failure_stage(report: dict, data: dict) -> str:
    if not report["login_detection"]:
        return "login"
    if not report["send_prompt"]:
        return "selector/send"
    if not report["wait_complete"]:
        return "wait"
    if not report["extract_answer"]:
        return "extract"
    if not report["answer_quality"].get("reliable"):
        return "answer_quality"
    return ""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


async def main():
    args = parse_args()
    result = await WebAISkill().execute(
        "请用一句话回答：local-ai-orchestrator 的目标是什么？",
        {"provider": "chatgpt", "headless": False, "max_followups": 1, "debug": args.debug},
    )
    data = result.to_dict()
    quality = answer_quality(data)
    metadata = data.get("metadata", {})
    report = {
        "provider": "chatgpt",
        "success": result.success,
        "login_detection": not data.get("metadata", {}).get("needs_login", False),
        "send_prompt": result.error is None
        or "selector" not in str(result.error).lower(),
        "wait_complete": bool(result.result),
        "extract_answer": bool(result.result),
        "answer_quality": quality,
        "follow_up": data.get("metadata", {}).get("followups", 0) >= 0,
        "evidence_saved": bool(result.evidence),
        "evidence_path": metadata.get("evidence_path", ""),
        "used_selector": metadata.get("used_selector", ""),
        "failure_stage": "",
        "fallback_result": data.get("metadata", {}).get("fallback"),
        "raw": data,
        "created_at": datetime.now().isoformat(),
    }
    report["failure_stage"] = failure_stage(report, data)
    out_dir = Path("runtime/test_reports/web_ai")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "chatgpt.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"REPORT={out}")


if __name__ == "__main__":
    asyncio.run(main())
