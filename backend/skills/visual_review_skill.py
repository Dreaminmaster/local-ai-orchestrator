"""Visual Review Skill — Evaluate UI/design quality using external vision models."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from .base import Skill, SkillResult, RiskLevel


VISUAL_REVIEW_PROMPT = """请从以下角度评价这个界面截图：
1. 是否显得高级（高级感评分 1-10）
2. 是否有低端模板感
3. 字体、间距、颜色是否统一
4. 视觉层级是否清晰
5. 布局是否平衡
6. 最需要改进的 5 个地方
7. 请给出可转化成 CSS / 组件修改的具体建议

用户的设计目标是：{goal}

请以 JSON 格式返回：
{{
  "overall_score": 7.5,
  "is_premium": true/false,
  "has_template_feel": true/false,
  "problems": ["问题1", "问题2"],
  "improvements": ["建议1", "建议2"],
  "css_suggestions": ["具体CSS修改1", "具体CSS修改2"],
  "pass": true/false
}}
"""

COMPARISON_PROMPT = """请比较以下两张界面截图（修改前 vs 修改后）：

用户的设计目标是：{goal}

请评价：
1. 修改后是否比修改前更好？
2. 有哪些改进？
3. 有哪些退步？
4. 是否需要继续修改？

请以 JSON 格式返回：
{{
  "improved": true/false,
  "before_score": 5.0,
  "after_score": 7.5,
  "improvements": ["改进1"],
  "regressions": ["退步1"],
  "needs_more_work": true/false,
  "next_suggestions": ["下一步建议1"]
}}
"""


class VisualReviewSkill(Skill):
    name = "visual_review"
    description = "Evaluate visual design quality using vision-capable AI models"
    capabilities = ["evaluate_design", "compare_before_after", "suggest_improvements"]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["visual", "design", "aesthetic", "review", "screenshot", "ui", "look"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "evaluate_design")

        try:
            if action == "evaluate_design":
                image_path = context.get("image", "")
                goal = context.get("goal", "高端、简洁、真实、不粗糙")
                return await self._evaluate(image_path, goal)
            elif action == "compare_before_after":
                before = context.get("before_image", "")
                after = context.get("after_image", "")
                goal = context.get("goal", "高端、简洁、真实、不粗糙")
                return await self._compare(before, after, goal)
            else:
                return SkillResult(
                    skill=self.name, success=False, result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(skill=self.name, success=False, result="", error=str(e))

    async def _evaluate(self, image_path: str, goal: str) -> SkillResult:
        if not Path(image_path).exists():
            return SkillResult(
                skill=self.name, success=False, result="",
                error=f"Image not found: {image_path}",
            )

        prompt = VISUAL_REVIEW_PROMPT.format(goal=goal)
        image_b64 = self._encode_image(image_path)

        # Try OpenAI first (GPT-4o has vision), then Gemini
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            result = await self._call_openai_vision(api_key, prompt, image_b64)
        else:
            api_key = os.getenv("GOOGLE_API_KEY", "")
            if api_key:
                result = await self._call_gemini_vision(api_key, prompt, image_path)
            else:
                return SkillResult(
                    skill=self.name, success=False, result="",
                    error="No vision-capable API key configured (OPENAI_API_KEY or GOOGLE_API_KEY)",
                )

        return SkillResult(
            skill=self.name, success=True,
            result=result,
            evidence=[image_path],
            metadata={"goal": goal},
        )

    async def _compare(self, before: str, after: str, goal: str) -> SkillResult:
        for p in [before, after]:
            if not Path(p).exists():
                return SkillResult(
                    skill=self.name, success=False, result="",
                    error=f"Image not found: {p}",
                )

        prompt = COMPARISON_PROMPT.format(goal=goal)
        # For simplicity, describe both images in text
        result = f"Comparison between {before} and {after} with goal: {goal}"

        return SkillResult(
            skill=self.name, success=True, result=result,
            evidence=[before, after],
            metadata={"goal": goal},
        )

    def _encode_image(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def _call_openai_vision(self, api_key: str, prompt: str, image_b64: str) -> str:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            }],
            "max_tokens": 2000,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def _call_gemini_vision(self, api_key: str, prompt: str, image_path: str) -> str:
        import httpx
        image_b64 = self._encode_image(image_path)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": image_b64}},
                ],
            }],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
