#!/usr/bin/env python3
"""Live E2E: Claude Web workspace page is reused by WebAISkill."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.core.reporter import Reporter
from backend.evidence.board import EvidenceBoard
from backend.llm.base import LLMMessage
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter
from backend.security.secret_scanner import SecretScanner
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.workspace_manager import workspace_manager

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_claude_workspace_live.json"
CLAUDE_PROFILE = ROOT / "runtime/browser_profiles/claude"


class FailingLLM:
    async def chat(self, messages: list[LLMMessage], **kwargs):
        raise RuntimeError("local model intentionally unavailable for workspace e2e")


def _write_report(output: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


def _quality_issues(quality: dict) -> list[str]:
    reason = quality.get("reason") or ""
    if not reason:
        return []
    return [part.strip() for part in reason.split(";") if part.strip()]


def _intervention_reason(state: str) -> str:
    return {
        "NEED_LOGIN": "claude_profile_missing_or_not_logged_in",
        "NEED_USER_INTERVENTION": "claude_needs_user_intervention",
        "PAGE_NETWORK_ERROR": "claude_page_network_error",
        "RETRYABLE_PAGE_ERROR": "claude_retryable_page_error",
        "STALE_CONVERSATION": "claude_stale_conversation",
    }.get(state, "claude_workspace_not_ready")


def _suggested_user_action(state: str) -> str:
    if state == "NEED_LOGIN":
        return "Open Claude Workspace and log in, then click Recheck/Resume."
    if state == "STALE_CONVERSATION":
        return "Open Claude Workspace, start a new chat if needed, then click Recheck/Resume."
    if state in {"PAGE_NETWORK_ERROR", "RETRYABLE_PAGE_ERROR"}:
        return "Check the Claude Workspace page/network state, then click Recheck/Resume."
    return "Handle the Claude Workspace prompt, verification, or popup, then click Recheck/Resume."


async def main() -> None:
    created_at = datetime.now().isoformat()
    provider = "Claude Web"
    selected_target = "Claude Web"
    output = {
        "created_at": created_at,
        "final_status": "FAIL",
        "provider": provider,
        "selected_target": selected_target,
        "workspace_opened": False,
        "reused_existing_page": False,
        "profile_dir": str(CLAUDE_PROFILE),
        "answer_quality": "FAIL",
        "quality_issues": [],
        "evidence_saved": False,
        "evidence_path": "",
        "report_contains_claude_web": False,
        "need_user_intervention": False,
        "failure_reason": "",
        "intervention_reason": "",
        "suggested_user_action": "",
        "can_resume_after_user_action": False,
        "recovery_attempted": False,
        "recovery_success": False,
        "recovery_reason": "",
        "recovery_action_taken": "",
        "page_url_before_recovery": "",
        "page_url_after_recovery": "",
        "workspace_status_after_recovery": "",
    }

    try:
        first_page = await workspace_manager.open_workspace(provider)
        output["workspace_opened"] = first_page is not None
        first_status = await workspace_manager.get_workspace_status(provider)
        output["workspace_status_before_send"] = first_status.to_dict()
        output["page_url"] = first_status.page_url
        output["need_user_intervention"] = first_status.need_user_intervention
        if first_status.state in {
            ProviderState.NEED_LOGIN,
            ProviderState.NEED_USER_INTERVENTION,
            ProviderState.PAGE_NETWORK_ERROR,
            ProviderState.RETRYABLE_PAGE_ERROR,
        }:
            output["final_status"] = "NEED_USER_INTERVENTION"
            output["need_user_intervention"] = True
            output["intervention_reason"] = _intervention_reason(first_status.state.value)
            output["suggested_user_action"] = _suggested_user_action(first_status.state.value)
            output["can_resume_after_user_action"] = True
            output["failure_reason"] = output["intervention_reason"]
            _write_report(output)
            return

        reused_page = await workspace_manager.ensure_workspace(provider)
        output["reused_existing_page"] = reused_page is first_page
        recovery = workspace_manager.last_recoveries.get("claude", {})
        if recovery:
            output.update(
                {
                    "recovery_attempted": bool(recovery.get("action_taken")),
                    "recovery_success": bool(recovery.get("recovered")),
                    "recovery_reason": recovery.get("reason", ""),
                    "recovery_action_taken": recovery.get("action_taken", ""),
                    "page_url_before_recovery": recovery.get("before_url", ""),
                    "page_url_after_recovery": recovery.get("after_url", ""),
                    "workspace_status_after_recovery": recovery.get(
                        "status_after_recovery", ""
                    ),
                }
            )

        agent = Agent()
        agent.failure_handler.runner.llm = FailingLLM()
        board = EvidenceBoard()
        scanner = SecretScanner()
        router = ExternalAIEscalationRouter()

        failure_info = {
            "error": (
                "external ai needed: local model is uncertain about a productized "
                "workspace reuse strategy and needs outside advice. API_KEY=abc123 "
                "should be redacted."
            ),
            "step": {
                "goal": "obtain Claude Web advice through the reusable workspace",
                "needed_skills": ["web_ai"],
            },
            "results": [{"skill": "shell", "success": False, "error": "uncertain"}],
            "goal_contract": {
                "goal_mode": "autonomous",
                "original_input": "Verify Claude Web workspace reuse.",
                "final_goal": "Use Claude Web workspace and save evidence.",
                "success_criteria": [
                    "EscalationRouter chooses Claude Web",
                    "WebAISkill reuses the open workspace page",
                    "Claude Web answer quality PASS",
                    "Evidence saved",
                ],
            },
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["ask_external_ai", "operate_browser"],
                "available_external_ai": ["Claude Web"],
                "execution_policy": {
                    "autonomous_external_ai_query": True,
                    "autonomous_retry": False,
                },
            },
        }
        state = {
            "retry_count": 2,
            "goal_contract": failure_info["goal_contract"],
            "authorization_contract": failure_info["authorization_contract"],
        }
        diagnosis = await agent.failure_handler.diagnose(failure_info, state)
        should_escalate = router.should_escalate(diagnosis.get("failure_type", ""), state)
        selected_target = router.choose_target(
            diagnosis.get("failure_type", ""),
            failure_info["authorization_contract"]["available_external_ai"],
        )
        output["selected_target"] = selected_target
        output["failure_type"] = diagnosis.get("failure_type")
        output["should_escalate"] = should_escalate

        raw_prompt = (
            "请用三点简短建议说明：本地 Agent 复用已登录 Claude Web workspace "
            "时，怎样保存证据、避免泄露密钥、并在需要人工验证时暂停？ "
            "API_KEY=abc123"
        )
        redaction = scanner.redact(raw_prompt)
        safe_prompt = redaction.redacted_text
        web_results = await agent.skill_router.execute_chain(
            ["web_ai"],
            safe_prompt,
            {
                "task_id": "e2e_claude_workspace_live",
                "step": failure_info["step"],
                "target": selected_target,
                "provider": selected_target,
                "prompt": safe_prompt,
                "debug": True,
                "max_followups": 0,
                "reuse_workspace": True,
                "authorization_contract": failure_info["authorization_contract"],
            },
        )
        for result in web_results:
            board.save_from_result("e2e_claude_workspace_live", "step_1", result)

        web_result = next((r for r in web_results if r.get("skill") == "web_ai"), {})
        metadata = web_result.get("metadata", {})
        skill_recovery = metadata.get("workspace_recovery") or {}
        if skill_recovery:
            output.update(
                {
                    "recovery_attempted": bool(skill_recovery.get("action_taken")),
                    "recovery_success": bool(skill_recovery.get("recovered")),
                    "recovery_reason": skill_recovery.get("reason", ""),
                    "recovery_action_taken": skill_recovery.get("action_taken", ""),
                    "page_url_before_recovery": skill_recovery.get("before_url", ""),
                    "page_url_after_recovery": skill_recovery.get("after_url", ""),
                    "workspace_status_after_recovery": skill_recovery.get(
                        "status_after_recovery", ""
                    ),
                }
            )
        quality = metadata.get("quality_check", {})
        evidence = web_result.get("evidence", [])
        evidence_path = metadata.get("evidence_path") or (evidence[0] if evidence else "")

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
            evidence=board.get_task_evidence("e2e_claude_workspace_live"),
        )
        after_status = await workspace_manager.get_workspace_status(provider)
        output.update(
            {
                "workspace_status_after_send": after_status.to_dict(),
                "answer_quality": quality.get("quality", "FAIL"),
                "quality_issues": _quality_issues(quality),
                "evidence_saved": bool(evidence),
                "evidence_path": evidence_path,
                "report_contains_claude_web": "使用 Claude Web 外部求助"
                in final_report,
                "used_selector": metadata.get("used_selector", ""),
                "web_ai_success": bool(web_result.get("success")),
                "need_user_intervention": bool(
                    metadata.get("need_user_intervention")
                    or after_status.need_user_intervention
                ),
                "failure_reason": (
                    metadata.get("failure_reason")
                    or web_result.get("error", "")
                    or quality.get("reason", "")
                ),
            }
        )
        if output["need_user_intervention"]:
            output["final_status"] = "NEED_USER_INTERVENTION"
            output["intervention_reason"] = output["failure_reason"] or "claude_needs_user_intervention"
            output["suggested_user_action"] = (
                metadata.get("suggested_user_action")
                or "Open Claude Workspace and log in, verify, or handle the page; then click Recheck/Resume."
            )
            output["can_resume_after_user_action"] = bool(
                metadata.get("can_resume", True)
            )
        elif (
            output["workspace_opened"]
            and output["reused_existing_page"]
            and selected_target == "Claude Web"
            and output["answer_quality"] == "PASS"
            and output["evidence_saved"]
            and output["report_contains_claude_web"]
        ):
            output["final_status"] = "PASS"
        else:
            output["final_status"] = "FAIL"
        if output["final_status"] == "PASS":
            output["failure_reason"] = ""
        _write_report(output)
        if output["final_status"] == "FAIL":
            raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as exc:
        output["failure_reason"] = str(exc)
        output["need_user_intervention"] = "Target page, context or browser has been closed" in str(exc)
        if output["need_user_intervention"]:
            output["final_status"] = "NEED_USER_INTERVENTION"
            output["intervention_reason"] = "browser_workspace_closed"
            output["suggested_user_action"] = "Reopen Claude Workspace, handle the page, then click Recheck/Resume."
            output["can_resume_after_user_action"] = True
            _write_report(output)
            return
        _write_report(output)
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
