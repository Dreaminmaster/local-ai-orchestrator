"""Skill wrapper for browser-based external AI asking."""
from backend.skills.base import Skill, SkillResult, RiskLevel
from .chatgpt_web_adapter import ChatGPTWebAdapter
from .claude_web_adapter import ClaudeWebAdapter
from .doubao_web_adapter import DoubaoWebAdapter
from .gemini_web_adapter import GeminiWebAdapter
from .kimi_web_adapter import KimiWebAdapter

ADAPTERS = {"chatgpt": ChatGPTWebAdapter, "claude": ClaudeWebAdapter, "doubao": DoubaoWebAdapter, "gemini": GeminiWebAdapter, "kimi": KimiWebAdapter}


class WebAISkill(Skill):
    name = "web_ai"
    description = "Ask logged-in external AI websites through persistent browser profiles"
    capabilities = ["ask_web_ai", "ask_chatgpt_web", "ask_claude_web", "ask_gemini_web", "ask_kimi_web", "ask_doubao_web"]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task: dict, state: dict) -> bool:
        return "web ai" in task.get("description", "").lower()

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        provider = context.get("provider") or context.get("target") or "chatgpt"
        prompt = context.get("question") or context.get("prompt") or instruction
        adapter_cls = ADAPTERS.get(provider)
        if not adapter_cls:
            return SkillResult(self.name, False, "", error=f"Unknown web AI provider: {provider}")
        response = await adapter_cls(profile_name=provider, headless=context.get("headless", False)).ask(prompt, context.get("attachments"))
        return SkillResult(
            skill=self.name,
            success=response.success,
            result=response.answer,
            evidence=response.evidence_files,
            error=response.error,
            needs_follow_up=response.needs_follow_up,
            suggested_next_action="login_required" if response.needs_login else None,
            metadata={"provider": provider, "needs_login": response.needs_login},
        )
