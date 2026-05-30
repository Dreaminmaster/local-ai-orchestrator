"""External AI Skill — Call external AI services (ChatGPT, Claude, Gemini, DeepSeek, etc.)."""

from __future__ import annotations
import json
import os
import httpx
from .base import Skill, SkillResult, RiskLevel

# External AI capability profiles
AI_PROFILES = {
    "chatgpt": {
        "name": "ChatGPT",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "model": "gpt-4o",
        "strengths": ["综合方案", "图像理解", "写作", "通用推理"],
        "best_for": ["通用问答", "创意写作", "图像分析"],
    },
    "claude": {
        "name": "Claude",
        "base_url": "https://api.anthropic.com/v1",
        "env_key": "ANTHROPIC_API_KEY",
        "model": "claude-sonnet-4-20250514",
        "strengths": ["长文分析", "复杂逻辑", "代码解释", "方案评审"],
        "best_for": ["复杂方案", "技术架构", "长文总结"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "strengths": ["代码能力强", "推理能力强", "中文优秀"],
        "best_for": ["代码生成", "数学推理", "中文任务"],
    },
    "gemini": {
        "name": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "env_key": "GOOGLE_API_KEY",
        "model": "gemini-2.0-flash",
        "strengths": ["视觉理解", "跨模态分析", "长上下文"],
        "best_for": ["视觉分析", "多模态任务"],
    },
}


class ExternalAISkill(Skill):
    name = "external_ai"
    description = "Query external AI services for expert opinions"
    capabilities = [
        "ask_chatgpt",
        "ask_claude",
        "ask_deepseek",
        "ask_gemini",
        "ask_best_for",
        "compare_answers",
    ]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = [
            "ask",
            "external",
            "chatgpt",
            "claude",
            "deepseek",
            "gemini",
            "expert",
            "opinion",
        ]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "ask_best_for")
        target = context.get("target", "")
        question = context.get("question", instruction)

        try:
            if action == "ask_best_for":
                # Auto-select the best AI for the task type
                task_type = context.get("task_type", "general")
                target = self._select_best_ai(task_type)
                return await self._ask_ai(target, question, context)
            elif action in ("ask_chatgpt", "ask_claude", "ask_deepseek", "ask_gemini"):
                target = action.replace("ask_", "")
                return await self._ask_ai(target, question, context)
            elif action == "compare_answers":
                return await self._compare(question, context)
            else:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(skill=self.name, success=False, result="", error=str(e))

    def _select_best_ai(self, task_type: str) -> str:
        """Select the best AI based on task type."""
        mapping = {
            "code": "deepseek",
            "code_review": "claude",
            "design": "chatgpt",
            "visual": "gemini",
            "analysis": "claude",
            "writing": "chatgpt",
            "math": "deepseek",
            "chinese": "deepseek",
            "general": "chatgpt",
        }
        return mapping.get(task_type, "chatgpt")

    async def _ask_ai(self, target: str, question: str, context: dict) -> SkillResult:
        profile = AI_PROFILES.get(target)
        if not profile:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Unknown AI target: {target}",
            )

        api_key = os.getenv(profile["env_key"], "")
        if not api_key:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"{profile['name']} API key not configured ({profile['env_key']})",
            )

        # Use OpenAI-compatible format for ChatGPT and DeepSeek
        if target in ("chatgpt", "deepseek"):
            return await self._call_openai_compatible(
                base_url=profile["base_url"],
                api_key=api_key,
                model=profile["model"],
                question=question,
                target_name=profile["name"],
            )
        elif target == "claude":
            return await self._call_anthropic(api_key, profile["model"], question)
        elif target == "gemini":
            return await self._call_gemini(api_key, profile["model"], question)

        return SkillResult(
            skill=self.name, success=False, result="", error="Unsupported target"
        )

    async def _call_openai_compatible(
        self, base_url: str, api_key: str, model: str, question: str, target_name: str
    ) -> SkillResult:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": question}],
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return SkillResult(
            skill=self.name,
            success=True,
            result=answer,
            metadata={"target": target_name, "model": model},
        )

    async def _call_anthropic(
        self, api_key: str, model: str, question: str
    ) -> SkillResult:
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": question}],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        answer = data["content"][0]["text"]
        return SkillResult(
            skill=self.name,
            success=True,
            result=answer,
            metadata={"target": "Claude", "model": model},
        )

    async def _call_gemini(
        self, api_key: str, model: str, question: str
    ) -> SkillResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": question}]}]}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        return SkillResult(
            skill=self.name,
            success=True,
            result=answer,
            metadata={"target": "Gemini", "model": model},
        )

    async def _compare(self, question: str, context: dict) -> SkillResult:
        """Ask multiple AIs and compare answers."""
        targets = context.get("targets", ["chatgpt", "claude"])
        results = {}
        for t in targets:
            r = await self._ask_ai(t, question, context)
            results[t] = r.result if r.success else f"[Error: {r.error}]"
        comparison = json.dumps(results, ensure_ascii=False, indent=2)
        return SkillResult(
            skill=self.name,
            success=True,
            result=comparison,
            metadata={"compared": targets},
        )
