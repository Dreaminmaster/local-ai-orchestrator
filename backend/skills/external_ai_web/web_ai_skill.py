"""Skill wrapper for browser-based external AI asking."""
from pathlib import Path
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
        provider = (context.get("provider") or context.get("target") or "chatgpt").lower()
        prompt = context.get("question") or context.get("prompt") or instruction
        adapter_cls = ADAPTERS.get(provider)
        if not adapter_cls:
            return SkillResult(self.name, False, "", error=f"Unknown web AI provider: {provider}")
        adapter = adapter_cls(profile_name=provider, headless=context.get("headless", False))
        response = await adapter.ask(prompt, context.get("attachments"))
        answers = [response.answer] if response.answer else []
        # Follow-up if answer is too short/vague and login succeeded.
        max_followups = int(context.get("max_followups", 1))
        for _ in range(max_followups):
            if not response.success or not response.needs_follow_up:
                break
            follow = "请把上一个回答转成更具体、可执行的步骤，并列出需要修改的文件、命令或 CSS/代码建议。"
            response = await adapter.ask(follow, None)
            if response.answer:
                answers.append(response.answer)
        evidence = list(response.evidence_files)
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
            suggested_next_action="login_required" if response.needs_login else None,
            metadata={"provider": provider, "needs_login": response.needs_login, "followups": max(0, len(answers)-1)},
        )
