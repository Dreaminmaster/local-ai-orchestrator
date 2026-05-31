#!/usr/bin/env python3
"""API-based external AI escalation E2E.

Requires OPENAI_API_KEY or ANTHROPIC_API_KEY env var.
Calls external_ai_skill directly (no browser).
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.evidence.board import EvidenceBoard
from backend.security.secret_scanner import SecretScanner

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_escalate_to_external_ai_api.json"


async def main():
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        msg = "No API keys configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
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

    provider = "chatgpt" if os.getenv("OPENAI_API_KEY") else "claude"
    result = await agent.skill_router.execute_chain(
        ["external_ai"],
        safe_prompt,
        {
            "task_id": "escalation_api_e2e",
            "step": {"goal": "external AI escalation via API"},
            "target": provider,
            "provider": provider,
            "question": safe_prompt,
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["ask_external_ai"],
                "available_external_ai": ["ChatGPT", "Claude"],
            },
        },
    )
    for r in result:
        board.save_from_result("escalation_api_e2e", "step_1", r)

    success = any(r.get("success") for r in result)
    answer = next((r.get("result", "") for r in result if r.get("success")), "")

    output = {
        "created_at": datetime.now().isoformat(),
        "provider": provider,
        "success": success,
        "redacted": redaction.redacted,
        "answer_preview": answer[:300] if answer else "",
        "evidence_ids": [
            e.get("id") for e in board.get_task_evidence("escalation_api_e2e")
        ],
        "status": "PASS" if success and answer else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if not success:
        print("NOTE: API call failed. Check API key and network.")


if __name__ == "__main__":
    asyncio.run(main())
