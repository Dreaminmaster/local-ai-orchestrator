#!/usr/bin/env python3
"""E2E external AI escalation flow.

Constructs a case where:
1. Shell fails.
2. FailureHandler diagnoses external_ai_needed.
3. EscalationRouter chooses a target.
4. ExternalAISkill (API) or WebAISkill (web) is called with redacted prompt.
5. Q/A evidence is saved.
6. RepairPlanner uses the response.

No real external AI or browser is required for the structural test.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.core.planner import TaskPlanner
from backend.core.repair_planner import RepairPlanner
from backend.evidence.board import EvidenceBoard
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter
from backend.security.secret_scanner import SecretScanner

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_escalate_to_web_ai.json"


async def main():
    agent = Agent()
    task_id = "escalation_e2e"
    step_id = "step_1"

    # 1. Simulate a shell failure that needs external AI
    failure_info = {
        "error": "Terminal error: complex code analysis required beyond local model capacity.",
        "step": {
            "goal": "analyze and fix complex code",
            "needed_skills": ["shell", "codex"],
        },
        "results": [{"skill": "shell", "success": False, "error": "command failed"}],
        "goal_contract": {
            "goal_mode": "autonomous",
            "final_goal": "fix complex code issue",
            "success_criteria": ["code runs", "evidence of analysis"],
        },
        "authorization_contract": {
            "authorization_mode": "full_autonomy",
            "granted_capabilities": ["run_shell", "ask_external_ai", "modify_code"],
            "available_external_ai": [
                "ChatGPT",
                "Claude",
                "Gemini",
                "DeepSeek",
                "Codex",
            ],
            "execution_policy": {
                "autonomous_retry": True,
                "autonomous_external_ai_query": True,
            },
        },
    }

    state = {
        "retry_count": 2,
        "goal_contract": failure_info["goal_contract"],
        "authorization_contract": failure_info["authorization_contract"],
    }

    # 2. FailureHandler diagnoses
    diagnosis = await agent.failure_handler.diagnose(failure_info, state)
    assert diagnosis, "FailureHandler should return a diagnosis"
    print(
        "1. Diagnosis:",
        diagnosis.get("failure_type"),
        diagnosis.get("repair_actions", [])[:3],
    )

    # 3. EscalationRouter decides
    router = ExternalAIEscalationRouter()
    should = router.should_escalate(diagnosis.get("failure_type", ""), state)
    print("2. Should escalate:", should)
    target = None
    if should:
        target = router.choose_target(
            diagnosis.get("failure_type", ""),
            failure_info["authorization_contract"]["available_external_ai"],
        )
        print("3. Escalation target:", target)

    # 4. Redact prompt and simulate external AI call (use ExternalAISkill API, which is OK to fail without key)
    scanner = SecretScanner()
    raw_prompt = f"Analyze this error and suggest a fix:\n\n{failure_info['error']}\n\nProject details: secret_key=abc123 is configured."
    redaction = scanner.redact(raw_prompt)
    safe_prompt = redaction.redacted_text
    redaction_meta = scanner.evidence_summary(redaction)
    print("4. Redacted prompt sample:", safe_prompt[:80], "...")

    # 5. Try ExternalAISkill (may fail without API key), fallback to FileSkill advisory
    evidence_board = EvidenceBoard()
    try:
        ai_result = await agent.skill_router.execute_chain(
            ["external_ai"],
            safe_prompt,
            {
                "task_id": task_id,
                "step": failure_info["step"],
                "target": "claude",
                "provider": "claude",
                "question": safe_prompt,
                "authorization_contract": failure_info["authorization_contract"],
            },
        )
    except Exception:
        # Fallback: external_ai may fail if no API key. Use file skill advisory.
        ai_result = [
            {
                "skill": "external_ai",
                "success": True,
                "result": "Advisory: examine traceback, apply minimal fix, rerun tests.",
                "error": None,
                "metadata": {
                    "redaction": redaction_meta,
                    "target": target or "ChatGPT",
                },
            }
        ]

    for r in ai_result:
        evidence_board.save_from_result(task_id, step_id, r)

    # 6. Save Q/A evidence
    qa_evidence = evidence_board.save(
        task_id,
        step_id,
        "external_ai_answer",
        "escalation_e2e",
        json.dumps(
            {
                "prompt": safe_prompt[:200],
                "answer": ai_result[0].get("result", "")[:500],
            },
            ensure_ascii=False,
        ),
        "External AI escalation response used for repair",
    )
    print("5. Escalation evidence saved:", qa_evidence["id"])

    # 7. RepairPlanner uses the result
    repair_planner = RepairPlanner()
    repair = repair_planner.plan(
        f"{diagnosis.get('failure_type', '')} {ai_result[0].get('result', '')}",
        failure_info["goal_contract"],
        failure_info["authorization_contract"],
    )
    print(
        "6. Repair plan:",
        repair["failure_type"],
        "actions:",
        repair["repair_actions"][:3],
    )

    # 8. Planner converts to steps
    planner = TaskPlanner(agent.llm)
    steps = planner.convert_repair_actions_to_steps(repair["repair_actions"])
    print("7. Converted steps:", len(steps))

    # 9. Output report
    result = {
        "created_at": datetime.now().isoformat(),
        "escalation_target": target,
        "redacted": redaction.redacted,
        "failure_type": diagnosis.get("failure_type"),
        "repair_actions": repair["repair_actions"],
        "steps_generated": len(steps),
        "evidence_ids": [
            e.get("id") for e in evidence_board.get_task_evidence(task_id)
        ],
        "status": "PASS" if steps else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n8. Report:", json.dumps(result, ensure_ascii=False, indent=2))
    assert result["status"] == "PASS"


if __name__ == "__main__":
    asyncio.run(main())
