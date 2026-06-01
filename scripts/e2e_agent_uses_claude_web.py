#!/usr/bin/env python3
"""E2E: Agent uses Claude Web as preferred escalation provider.

Runs a simple failure -> escalation -> Claude Web -> answer -> evidence chain.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.evidence.board import EvidenceBoard
from backend.security.secret_scanner import SecretScanner
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_agent_uses_claude_web.json"


async def main():
    agent = Agent()
    board = EvidenceBoard()
    scanner = SecretScanner()
    router = ExternalAIEscalationRouter()
    task_id = "claude_web_e2e"

    target = router.choose_target(
        "code_repair_failed", ["Claude Web", "ChatGPT", "Codex"]
    )
    print(f"Selected target: {target}")

    prompt = (
        "In one short sentence, what is the primary purpose of local-ai-orchestrator?"
    )
    redaction = scanner.redact(prompt)
    safe_prompt = redaction.redacted_text

    result = await agent.skill_router.execute_chain(
        ["web_ai"],
        safe_prompt,
        {
            "task_id": task_id,
            "step": {"goal": "test Claude Web escalation"},
            "provider": (target or "claude").lower(),
            "target": target,
            "question": safe_prompt,
            "headless": False,
            "max_followups": 1,
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["ask_external_ai", "operate_browser"],
                "available_external_ai": ["Claude Web", "ChatGPT"],
            },
        },
    )

    for r in result:
        board.save_from_result(task_id, "step_1", r)

    success = any(r.get("success") for r in result)
    answer = next((r.get("result", "") for r in result if r.get("success")), "")
    metadata = next((r.get("metadata", {}) for r in result), {})

    report = {
        "created_at": datetime.now().isoformat(),
        "final_status": "PASS" if success else "FAIL",
        "selected_target": target,
        "answer_preview": answer[:300] if answer else "",
        "evidence_saved": bool(answer),
        "report_contains_claude_web": "claude" in answer.lower()
        or "web_ai" in str(metadata),
        "status": "PASS" if success and answer else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
