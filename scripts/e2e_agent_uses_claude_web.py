#!/usr/bin/env python3
"""E2E: Agent escalation selects and uses Claude Web."""

from __future__ import annotations

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.core.reporter import Reporter
from backend.evidence.board import EvidenceBoard
from backend.llm.base import LLMMessage
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter
from backend.security.secret_scanner import SecretScanner

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_agent_uses_claude_web.json"
CLAUDE_PROFILE = ROOT / "runtime/browser_profiles/claude"


class FailingLLM:
    async def chat(self, messages: list[LLMMessage], **kwargs):
        raise RuntimeError("local model intentionally unavailable for e2e fallback")


def parse_args():
    parser = argparse.ArgumentParser(
        description="E2E: Agent escalation selects and uses Claude Web."
    )
    parser.add_argument(
        "--force-provider",
        "--target",
        dest="force_provider",
        default="",
        help="Force a provider target for clean-clone E2E setup, e.g. 'Claude Web'.",
    )
    return parser.parse_args()


def _normalize_provider(value: str) -> str:
    return (value or "").strip()


def _is_claude_web(value: str) -> bool:
    return _normalize_provider(value).lower().replace("_", " ") in {
        "claude",
        "claude web",
    }


def _write_output(output: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


async def main():
    args = parse_args()
    requested_provider = _normalize_provider(args.force_provider)
    force_provider = bool(requested_provider)
    agent = Agent()
    agent.failure_handler.runner.llm = FailingLLM()
    board = EvidenceBoard()
    scanner = SecretScanner()
    task_id = "agent_uses_claude_web"
    step_id = "step_1"

    failure_info = {
        "error": (
            "external ai needed: local model is uncertain about a nuanced repair "
            "strategy and needs outside advice. API_KEY=abc123 should be redacted."
        ),
        "step": {
            "goal": "obtain external advice for a nuanced local repair",
            "needed_skills": ["web_ai"],
        },
        "results": [{"skill": "shell", "success": False, "error": "uncertain"}],
        "goal_contract": {
            "goal_mode": "autonomous",
            "original_input": "Use external web AI for advice when local model is uncertain.",
            "final_goal": "Get reliable external advice and save evidence.",
            "success_criteria": [
                "FailureHandler returns external_ai_needed",
                "EscalationRouter chooses Claude Web",
                "Claude Web answer quality PASS",
                "Evidence saved",
            ],
        },
        "authorization_contract": {
            "authorization_mode": "full_autonomy",
            "granted_capabilities": ["ask_external_ai", "operate_browser"],
            "available_external_ai": ["ChatGPT", "Claude"],
            "execution_policy": {
                "autonomous_external_ai_query": True,
                "autonomous_retry": True,
            },
        },
    }
    state = {
        "retry_count": 2,
        "goal_contract": failure_info["goal_contract"],
        "authorization_contract": failure_info["authorization_contract"],
    }

    diagnosis = await agent.failure_handler.diagnose(failure_info, state)
    router = ExternalAIEscalationRouter()
    should_escalate = router.should_escalate(diagnosis.get("failure_type", ""), state)
    provider_status_source = "runtime_report"
    skipped_reason = ""
    if force_provider:
        if not _is_claude_web(requested_provider):
            skipped_reason = "unsupported_forced_provider"
            output = {
                "created_at": datetime.now().isoformat(),
                "force_provider": True,
                "requested_provider": requested_provider,
                "provider_status_source": "forced_cli_argument",
                "skipped_reason": skipped_reason,
                "selected_target": None,
                "status": "SKIP",
            }
            _write_output(output)
            return
        if not CLAUDE_PROFILE.exists():
            skipped_reason = "claude_profile_missing_or_not_logged_in"
            output = {
                "created_at": datetime.now().isoformat(),
                "failure_type": diagnosis.get("failure_type"),
                "should_escalate": should_escalate,
                "force_provider": True,
                "requested_provider": requested_provider,
                "provider_status_source": "forced_cli_argument",
                "skipped_reason": skipped_reason,
                "selected_target": "Claude Web",
                "provider_profile": "runtime/browser_profiles/claude",
                "web_ai_success": False,
                "answer_quality": {"passed": False, "reason": skipped_reason, "quality": "FAIL"},
                "evidence_saved": False,
                "evidence": [],
                "final_report_contains_claude_web": False,
                "status": "SKIP",
            }
            _write_output(output)
            return
        target = "Claude Web"
        provider_status_source = "forced_cli_argument"
    else:
        target = router.choose_target(
            diagnosis.get("failure_type", ""),
            failure_info["authorization_contract"]["available_external_ai"],
        )

    raw_prompt = (
        "请给一个简短、可执行的建议：当本地 Agent 不确定修复方案时，"
        "应该如何安全地使用外部 AI？ API_KEY=abc123"
    )
    redaction = scanner.redact(raw_prompt)
    safe_prompt = redaction.redacted_text

    web_results = await agent.skill_router.execute_chain(
        ["web_ai"],
        safe_prompt,
        {
            "task_id": task_id,
            "step": failure_info["step"],
            "target": target,
            "provider": target,
            "prompt": safe_prompt,
            "debug": True,
            "max_followups": 0,
            "authorization_contract": failure_info["authorization_contract"],
        },
    )

    for result in web_results:
        board.save_from_result(task_id, step_id, result)

    web_result = next((r for r in web_results if r.get("skill") == "web_ai"), {})
    metadata = web_result.get("metadata", {})
    quality = metadata.get("quality_check", {})
    evidence_saved = bool(web_result.get("evidence"))

    reporter = Reporter(FailingLLM())
    final_report = await reporter.generate_with_contracts(
        failure_info["goal_contract"],
        failure_info["authorization_contract"],
        steps=[
            {
                "skill": "web_ai",
                "success": web_result.get("success"),
                "provider": "Claude Web",
                "result": web_result.get("result", ""),
                "metadata": metadata,
            }
        ],
        evidence=board.get_task_evidence(task_id),
    )

    output = {
        "created_at": datetime.now().isoformat(),
        "failure_type": diagnosis.get("failure_type"),
        "should_escalate": should_escalate,
        "force_provider": force_provider,
        "requested_provider": requested_provider,
        "selected_target": target,
        "provider_status_source": provider_status_source,
        "skipped_reason": skipped_reason,
        "provider_profile": "runtime/browser_profiles/claude",
        "redacted": redaction.redacted,
        "safe_prompt_preview": safe_prompt[:200],
        "web_ai_success": bool(web_result.get("success")),
        "answer_quality": quality,
        "evidence_saved": evidence_saved,
        "evidence": web_result.get("evidence", []),
        "final_report_contains_claude_web": "使用 Claude Web 外部求助" in final_report,
        "final_report_preview": final_report[:1200],
    }
    output["status"] = (
        "PASS"
        if output["failure_type"] == "external_ai_needed"
        and output["should_escalate"]
        and output["selected_target"] == "Claude Web"
        and output["web_ai_success"]
        and output["answer_quality"].get("quality") == "PASS"
        and output["evidence_saved"]
        and output["final_report_contains_claude_web"]
        else "FAIL"
    )

    login_required = (
        force_provider
        and output["selected_target"] == "Claude Web"
        and output["answer_quality"].get("reason") == "Login required"
    )
    if login_required:
        output["skipped_reason"] = "claude_profile_missing_or_not_logged_in"
    _write_output(output)
    if output["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
