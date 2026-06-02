#!/usr/bin/env python3
"""E2E: Agent uses Claude Web as forced escalation provider.

Usage:
    PYTHONPATH=. python scripts/e2e_agent_uses_claude_web.py --force-provider "Claude Web"

Without --force-provider, runs the dynamic escalation router.
"""

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force-provider",
        default=None,
        help="Force a specific provider (e.g. 'Claude Web')",
    )
    args = parser.parse_args()

    agent = Agent()
    board = EvidenceBoard()
    scanner = SecretScanner()
    router = ExternalAIEscalationRouter()
    task_id = "claude_web_e2e"

    if args.force_provider:
        target = args.force_provider
        provider_status_source = "forced_cli_argument"
        skipped_reason = None
        requested_provider = args.force_provider
    else:
        candidates = ["Claude Web", "ChatGPT", "Codex"]
        target = router.choose_target("code_repair_failed", candidates)
        provider_status_source = "escalation_router_dynamic"
        skipped_reason = "router returned None" if target is None else None
        requested_provider = None

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
    aq = metadata.get("answer_quality", {})

    final_status = "PASS" if success else "FAIL"

    report = {
        "created_at": datetime.now().isoformat(),
        "final_status": final_status,
        "selected_target": target,
        "provider_status_source": provider_status_source,
        "requested_provider": requested_provider,
        "skipped_reason": skipped_reason,
        "answer_preview": answer[:300] if answer else "",
        "answer_quality": aq.get("quality", "PASS" if success else "FAIL"),
        "evidence_saved": bool(answer),
        "report_contains_claude_web": "claude" in answer.lower(),
        "status": final_status,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
