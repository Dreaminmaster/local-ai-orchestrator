"""Skill wrapper for browser-based external AI asking."""

from pathlib import Path

from backend.skills.base import Skill, SkillResult, RiskLevel
from backend.skills.desktop_visual.desktop_visual_skill import DesktopVisualSkill
from backend.security.secret_scanner import SecretScanner
from .chatgpt_web_adapter import ChatGPTWebAdapter
from .claude_web_adapter import ClaudeWebAdapter
from .doubao_web_adapter import DoubaoWebAdapter
from .gemini_web_adapter import GeminiWebAdapter
from .kimi_web_adapter import KimiWebAdapter
from .evidence_writer import WebAIEvidenceWriter
from .answer_quality_check import AnswerQualityChecker
from .workspace_manager import workspace_manager
from .provider_status import ProviderState
from .pending_action import pending_external_ai_store

ADAPTERS = {
    "chatgpt": ChatGPTWebAdapter,
    "claude": ClaudeWebAdapter,
    "doubao": DoubaoWebAdapter,
    "gemini": GeminiWebAdapter,
    "kimi": KimiWebAdapter,
}
PROFILE_NAMES = {
    "chatgpt": "chatgpt",
    "claude": "claude",
    "doubao": "doubao",
    "gemini": "gemini",
    "kimi": "kimi",
}

INTERVENTION_ACTIONS = {
    "NEED_LOGIN": "Open the provider workspace and log in, then click Recheck/Resume.",
    "NEED_USER_INTERVENTION": "Handle the provider verification or popup, then click Recheck/Resume.",
    "PAGE_NETWORK_ERROR": "Check the provider page or network banner, then click Recheck/Resume.",
    "RETRYABLE_PAGE_ERROR": "Handle the provider page error, then click Recheck/Resume.",
    "STALE_CONVERSATION": "Start a fresh provider chat, then click Recheck/Resume.",
    "UNKNOWN_ERROR": "Inspect the provider workspace, then click Recheck/Resume.",
}

PROVIDER_ALIASES = {
    "claude web": "claude",
    "claude_web": "claude",
    "chatgpt web": "chatgpt",
    "chatgpt_web": "chatgpt",
    "gemini web": "gemini",
    "gemini_web": "gemini",
    "kimi web": "kimi",
    "kimi_web": "kimi",
    "doubao web": "doubao",
    "doubao_web": "doubao",
    "豆包 web": "doubao",
}


class WebAISkill(Skill):
    name = "web_ai"
    description = (
        "Ask logged-in external AI websites through persistent browser profiles"
    )
    capabilities = [
        "ask_web_ai",
        "ask_chatgpt_web",
        "ask_claude_web",
        "ask_gemini_web",
        "ask_kimi_web",
        "ask_doubao_web",
    ]
    risk_level = RiskLevel.LOW

    def __init__(self):
        self.evidence_writer = WebAIEvidenceWriter()
        self.secret_scanner = SecretScanner()
        self.quality_checker = AnswerQualityChecker()

    async def can_handle(self, task: dict, state: dict) -> bool:
        return "web ai" in task.get("description", "").lower()

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        provider = (
            context.get("provider") or context.get("target") or "chatgpt"
        ).lower()
        provider = PROVIDER_ALIASES.get(provider, provider)
        if context.get("_workspace_lock_held") or not hasattr(
            workspace_manager, "provider_request"
        ):
            return await self._execute_owned(instruction, context)
        async with workspace_manager.provider_request(
            provider, context.get("request_id", "")
        ) as request_id:
            owned_context = dict(context)
            owned_context["_workspace_lock_held"] = True
            owned_context["request_id"] = request_id
            result = await self._execute_owned(instruction, owned_context)
            result.metadata.update(
                {
                    "request_id": request_id,
                    "profile_owner": "backend",
                    "workspace_reused": workspace_manager.workspace_reused.get(
                        provider, False
                    ),
                    "second_context_created": False,
                }
            )
            return result

    async def _execute_owned(self, instruction: str, context: dict) -> SkillResult:
        provider = (
            context.get("provider") or context.get("target") or "chatgpt"
        ).lower()
        provider = PROVIDER_ALIASES.get(provider, provider)
        original_prompt = context.get("question") or context.get("prompt") or instruction
        redaction = self.secret_scanner.redact(original_prompt)
        prompt = redaction.redacted_text
        redaction_meta = self.secret_scanner.evidence_summary(redaction)
        adapter_cls = ADAPTERS.get(provider)
        if not adapter_cls:
            return SkillResult(
                self.name, False, "", error=f"Unknown web AI provider: {provider}"
            )
        page = None
        workspace_status = None
        workspace_recovery = {}
        if context.get("reuse_workspace", True):
            try:
                page = await workspace_manager.ensure_workspace(provider)
                workspace_status = workspace_manager.last_statuses.get(provider)
                workspace_recovery = workspace_manager.last_recoveries.get(provider, {})
                if workspace_status and workspace_status.state in {
                    ProviderState.NEED_LOGIN,
                    ProviderState.NEED_USER_INTERVENTION,
                    ProviderState.STALE_CONVERSATION,
                    ProviderState.PAGE_NETWORK_ERROR,
                    ProviderState.RETRYABLE_PAGE_ERROR,
                    ProviderState.UNKNOWN_ERROR,
                }:
                    status_value = workspace_status.state.value
                    failure_reason = (
                        "claude_profile_missing_or_not_logged_in"
                        if provider == "claude" and workspace_status.state == ProviderState.NEED_LOGIN
                        else status_value.lower()
                    )
                    suggested_user_action = INTERVENTION_ACTIONS.get(
                        status_value,
                        "Handle the provider workspace, then click Recheck/Resume.",
                    )
                    task_id = context.get("task_id", "external_ai_manual")
                    step_id = f"step_{int(context.get('step_index', 0)) + 1}"
                    pending = pending_external_ai_store.save(
                        task_id=task_id,
                        step_id=step_id,
                        provider=provider,
                        original_prompt=original_prompt,
                        redacted_prompt=prompt,
                        context=context,
                        provider_status=status_value,
                        failure_reason=failure_reason,
                        suggested_user_action=suggested_user_action,
                        can_resume=True,
                    )
                    return SkillResult(
                        skill=self.name,
                        success=False,
                        result="",
                        error=failure_reason,
                        needs_follow_up=True,
                        suggested_next_action="user_intervention_required",
                        metadata={
                            "provider": provider,
                            "provider_status": status_value,
                            "failure_reason": failure_reason,
                            "suggested_user_action": suggested_user_action,
                            "can_resume": True,
                            "pending_external_ai": pending,
                            "workspace_status": workspace_status.to_dict(),
                            "workspace_recovery": workspace_recovery,
                            "need_user_intervention": True,
                        },
                    )
            except Exception as exc:
                workspace_recovery = {"error": str(exc)}
                failure_reason = (
                    "PROFILE_IN_USE_BY_BACKEND"
                    if "PROFILE_IN_USE_BY_BACKEND" in str(exc)
                    else "workspace_open_failed"
                )
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=failure_reason,
                    needs_follow_up=True,
                    suggested_next_action="use_backend_workspace_api",
                    metadata={
                        "provider": provider,
                        "failure_reason": failure_reason,
                        "workspace_recovery": workspace_recovery,
                        "need_user_intervention": False,
                        "profile_owner": "backend",
                        "second_context_created": False,
                    },
                )
        adapter = adapter_cls(
            page=page,
            profile_name=PROFILE_NAMES.get(provider, provider),
            headless=context.get("headless", False),
            debug=context.get("debug", False),
        )
        answers, evidence = [], []
        try:
            response = await adapter.ask(prompt, context.get("attachments"))
            result_text = response.answer
            # Answer quality check
            quality_check_meta = self._check_answer_quality(response)
            run_metadata = self._run_metadata(
                provider, response, quality_check_meta, redaction_meta
            )
            run_evidence = await self.evidence_writer.save_run(
                provider,
                prompt,
                result_text,
                page=getattr(adapter, "page", None),
                metadata=run_metadata,
            )
            evidence.append(run_evidence)
            if response.needs_login:
                failure_reason = (
                    "claude_login_required" if provider == "claude" else "provider_login_required"
                )
                task_id = context.get("task_id", "external_ai_manual")
                step_id = f"step_{int(context.get('step_index', 0)) + 1}"
                pending = pending_external_ai_store.save(
                    task_id=task_id,
                    step_id=step_id,
                    provider=provider,
                    original_prompt=original_prompt,
                    redacted_prompt=prompt,
                    context=context,
                    provider_status="NEED_LOGIN",
                    failure_reason=failure_reason,
                    suggested_user_action=INTERVENTION_ACTIONS["NEED_LOGIN"],
                    can_resume=True,
                )
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=failure_reason,
                    evidence=evidence + response.evidence_files,
                    needs_follow_up=True,
                    suggested_next_action="user_intervention_required",
                    metadata={
                        "provider": provider,
                        "quality_check": quality_check_meta,
                        "evidence_path": run_evidence,
                        "used_selector": "",
                        "send": {},
                        "extract": {},
                        "redaction": redaction_meta,
                        "workspace_status": workspace_status.to_dict()
                        if workspace_status
                        else {},
                        "workspace_recovery": workspace_recovery,
                        "need_user_intervention": True,
                        "failure_reason": failure_reason,
                        "provider_status": "NEED_LOGIN",
                        "suggested_user_action": INTERVENTION_ACTIONS["NEED_LOGIN"],
                        "can_resume": True,
                        "pending_external_ai": pending,
                    },
                )
            if context.get("debug"):
                try:
                    debug_dir = Path(run_evidence)
                    await adapter.page.screenshot(
                        path=str(debug_dir / "screenshot_after_answer.png"),
                        full_page=True,
                    )
                    (debug_dir / "candidate_selectors.json").write_text(
                        __import__("json").dumps(
                            response.metadata.get("extract", {}).get(
                                "candidate_selectors", []
                            )
                            if response.metadata
                            else [],
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
            if not quality_check_meta["passed"]:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result=result_text,
                    error=f"Answer quality check failed: {quality_check_meta['reason']}",
                    evidence=evidence + response.evidence_files,
                    needs_follow_up=True,
                    suggested_next_action="retry_or_escalate",
                    metadata={
                        "provider": provider,
                        "quality_check": quality_check_meta,
                        "evidence_path": run_evidence,
                        "used_selector": (response.metadata or {})
                        .get("extract", {})
                        .get("used_selector", ""),
                        "send": (response.metadata or {}).get("send", {}),
                        "extract": (response.metadata or {}).get("extract", {}),
                        "redaction": redaction_meta,
                        "workspace_status": workspace_status.to_dict()
                        if workspace_status
                        else {},
                        "workspace_recovery": workspace_recovery,
                        "need_user_intervention": False,
                    },
                )

            if response.answer:
                answers.append(response.answer)
            max_followups = int(context.get("max_followups", 1))
            for _ in range(max_followups):
                if not response.success or not response.needs_follow_up:
                    break
                follow = "请把上一个回答转成更具体、可执行的步骤，并列出需要修改的文件、命令或 CSS/代码建议。"
                response = await adapter.ask(follow, None)
                if response.answer:
                    answers.append(response.answer)
            evidence.extend(response.evidence_files)
            if answers:
                evidence.append(
                    self.evidence_writer.save_qa(
                        provider,
                        prompt,
                        "\n\n--- FOLLOW UP ---\n\n".join(answers),
                        {
                            "followups": max(0, len(answers) - 1),
                            "redaction": redaction_meta,
                        },
                    )
                )
            try:
                Path("runtime/evidence").mkdir(parents=True, exist_ok=True)
                shot = f"runtime/evidence/{provider}_conversation.png"
                await adapter.page.screenshot(path=shot, full_page=True)
                evidence.append(shot)
            except Exception:
                pass
            return SkillResult(
                skill=self.name,
                success=bool(answers) and not response.needs_login,
                result="\n\n--- FOLLOW UP ---\n\n".join(answers),
                evidence=evidence,
                error=response.error,
                needs_follow_up=response.needs_follow_up,
                suggested_next_action=(
                    "login_required" if response.needs_login else None
                ),
                metadata={
                    "provider": provider,
                    "needs_login": response.needs_login,
                    "followups": max(0, len(answers) - 1),
                    "profile": PROFILE_NAMES.get(provider, provider),
                    "evidence_path": run_evidence,
                    "quality_check": quality_check_meta,
                    "used_selector": (response.metadata or {})
                    .get("extract", {})
                    .get("used_selector", ""),
                    "send": (response.metadata or {}).get("send", {}),
                    "extract": (response.metadata or {}).get("extract", {}),
                    "redaction": redaction_meta,
                    "workspace_status": workspace_status.to_dict()
                    if workspace_status
                    else {},
                    "workspace_recovery": workspace_recovery,
                    "need_user_intervention": False,
                },
            )
        except Exception as exc:
            # selector/page failure fallback: capture desktop screenshot to aid visual operation.
            fallback_evidence = []
            evidence_path = ""
            try:
                evidence_path = await self.evidence_writer.save_run(
                    provider,
                    prompt,
                    "",
                    page=getattr(adapter, "page", None),
                    metadata={
                        "provider": provider,
                        "profile_dir": str(
                            Path("runtime/browser_profiles")
                            / PROFILE_NAMES.get(provider, provider)
                        ),
                        "send_success": False,
                        "extract_success": False,
                        "answer_quality": "FAIL",
                        "quality_issues": [str(exc)],
                        "used_selector": "",
                        "created_at": __import__("datetime").datetime.now().isoformat(),
                    },
                )
                fallback_evidence.append(evidence_path)
            except Exception:
                pass
            try:
                desktop_result = await DesktopVisualSkill().execute(
                    "observe current AI web page after selector failure",
                    {
                        "action": "observe_screen",
                        "save_as": f"runtime/evidence/{provider}_selector_failed.png",
                    },
                )
                fallback_evidence.extend(desktop_result.evidence)
            except Exception:
                pass
            return SkillResult(
                self.name,
                False,
                "",
                evidence=fallback_evidence,
                error=f"web_ai selector/page failure: {exc}",
                needs_follow_up=True,
                suggested_next_action="fallback_to_desktop_visual",
                metadata={
                    "provider": provider,
                    "fallback": "desktop_visual",
                    "evidence_path": evidence_path,
                    "failure_stage": "selector_send_or_page",
                },
            )

    def _check_answer_quality(self, response) -> dict:
        answer = response.answer or ""
        if response.needs_login:
            return {"passed": False, "reason": "", "quality": "BLOCKED"}
        extract = (response.metadata or {}).get("extract", {})
        used_selector = extract.get("used_selector", "")
        unreliable_source = bool(
            extract.get("body_fallback")
            or used_selector == "body_fallback"
            or used_selector.startswith("body_marker:")
        )
        quality = self.quality_checker.check(
            answer,
            reliable_answer=not unreliable_source,
            warning_text=extract.get("warning_text", ""),
            warning_class=extract.get("warning_class", ""),
        )
        if unreliable_source and "body_fallback" not in quality["issues"]:
            quality["issues"].append("body_fallback")
        if not quality["reliable"]:
            reasons = "; ".join(quality["issues"])
            return {"passed": False, "reason": reasons, "quality": quality["quality"]}
        return {
            "passed": True,
            "reason": "",
            "quality": quality["quality"],
            "warning_class": quality.get("warning_class", ""),
            "warning_text": quality.get("warning_text", ""),
        }

    def _run_metadata(self, provider, response, quality_check_meta, redaction_meta):
        profile = PROFILE_NAMES.get(provider, provider)
        extract = (response.metadata or {}).get("extract", {})
        send = (response.metadata or {}).get("send", {})
        return {
            "provider": provider,
            "profile_dir": str(Path("runtime/browser_profiles") / profile),
            "send_success": bool(send.get("send_success")),
            "extract_success": bool(response.answer),
            "answer_quality": quality_check_meta.get("quality"),
            "quality_issues": [quality_check_meta.get("reason")]
            if quality_check_meta.get("reason")
            else [],
            "used_selector": extract.get("used_selector", ""),
            "answer_selector": extract.get("used_selector", ""),
            "answer_timestamp": extract.get("answer_timestamp", ""),
            "prompt_timestamp": send.get("prompt_timestamp", ""),
            "warning_text": extract.get("warning_text", ""),
            "warning_class": extract.get("warning_class", ""),
            "quality_result": quality_check_meta,
            "body_fallback": extract.get("body_fallback", False),
            "error_reason": extract.get("error_reason", ""),
            "send": send,
            "extract": extract,
            "redaction": redaction_meta,
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }
