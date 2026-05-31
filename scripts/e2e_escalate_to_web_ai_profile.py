#!/usr/bin/env python3
"""Web AI profile-based external AI escalation E2E.

Requires a logged-in Playwright persistent profile for the chosen provider.
Uses WebAISkill (browser) to ask the external AI.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.evidence.board import EvidenceBoard
from backend.security.secret_scanner import SecretScanner

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_escalate_to_web_ai_profile.json"
PROFILE_STATUS = ROOT / "runtime/test_reports/web_ai/profile_status.json"


async def main():
    provider = "chatgpt"
    if PROFILE_STATUS.exists():
        status = json.loads(PROFILE_STATUS.read_text(encoding="utf-8"))
        available = [p for p, s in status.items() if s.get("logged_in")]
        if available:
            provider = available[0]
        else:
            msg = "No logged-in provider found. Run init_web_ai_profile.py first."
            print(
                json.dumps(
                    {"status": "SKIP", "reason": msg}, ensure_ascii=False, indent=2
                )
            )
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(
                json.dumps(
                    {
                        "status": "SKIP",
                        "reason": msg,
                        "created_at": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
    else:
        msg = "No profile status file found. Run init_web_ai_profile.py first."
        print(
            json.dumps({"status": "SKIP", "reason": msg}, ensure_ascii=False, indent=2)
        )
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(
                {
                    "status": "SKIP",
                    "reason": msg,
                    "created_at": datetime.now().isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    agent = Agent()
    board = EvidenceBoard()
    scanner = SecretScanner()

    prompt = "In one sentence, what is a good strategy for debugging Python NameError?"
    redaction = scanner.redact(prompt)
    safe_prompt = redaction.redacted_text

    try:
        result = await agent.skill_router.execute_chain(
            ["web_ai"],
            safe_prompt,
            {
                "task_id": "escalation_web_e2e",
                "step": {"goal": "external AI escalation via web profile"},
                "provider": provider,
                "target": provider,
                "question": safe_prompt,
                "headless": False,
                "max_followups": 1,
                "authorization_contract": {
                    "authorization_mode": "full_autonomy",
                    "granted_capabilities": ["ask_external_ai", "operate_browser"],
                    "available_external_ai": ["ChatGPT", "Claude"],
                },
            },
        )
    except Exception as exc:
        result = [
            {"skill": "web_ai", "success": False, "result": "", "error": str(exc)}
        ]

    for r in result:
        board.save_from_result("escalation_web_e2e", "step_1", r)

    success = any(r.get("success") for r in result)
    answer = next((r.get("result", "") for r in result if r.get("success")), "")
    error = next((r.get("error", "") for r in result if r.get("error")), "")

    output = {
        "created_at": datetime.now().isoformat(),
        "provider": provider,
        "success": success,
        "redacted": redaction.redacted,
        "answer_preview": answer[:300] if answer else "",
        "error": error[:300] if error else "",
        "evidence_ids": [
            e.get("id") for e in board.get_task_evidence("escalation_web_e2e")
        ],
        "status": "PASS" if success and answer else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
