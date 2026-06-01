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

PROVIDER_ALIASES = {
    "claude web": "claude",
    "claude_web": "claude",
    "chatgpt web": "chatgpt",
    "chatgpt_web": "chatgpt",
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
        prompt = context.get("question") or context.get("prompt") or instruction
        redaction = self.secret_scanner.redact(prompt)
        prompt = redaction.redacted_text
        redaction_meta = self.secret_scanner.evidence_summary(redaction)
        adapter_cls = ADAPTERS.get(provider)
        if not adapter_cls:
            return SkillResult(
                self.name, False, "", error=f"Unknown web AI provider: {provider}"
            )
        adapter = adapter_cls(
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
            return {"passed": False, "reason": "Login required", "quality": "FAIL"}
        quality = self.quality_checker.check(answer)
        if response.metadata and response.metadata.get("extract", {}).get("body_fallback"):
            quality["quality"] = "PARTIAL"
            quality["reliable"] = False
            if "body_fallback" not in quality["issues"]:
                quality["issues"].append("body_fallback")
        if not quality["reliable"]:
            reasons = "; ".join(quality["issues"])
            return {"passed": False, "reason": reasons, "quality": quality["quality"]}
        return {"passed": True, "reason": "", "quality": "PASS"}

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
            "body_fallback": extract.get("body_fallback", False),
            "error_reason": extract.get("error_reason", ""),
            "send": send,
            "extract": extract,
            "redaction": redaction_meta,
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }
