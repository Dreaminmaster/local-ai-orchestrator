"""Search Skill — Web search via DuckDuckGo."""
from __future__ import annotations
import json
from .base import Skill, SkillResult, RiskLevel


class SearchSkill(Skill):
    name = "search"
    description = "Search the web for information using DuckDuckGo"
    capabilities = ["web_search", "news_search"]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["search", "find", "lookup", "latest", "recent", "information"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        query = context.get("query", instruction)
        max_results = context.get("max_results", 5)
        search_type = context.get("search_type", "text")

        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return SkillResult(
                skill=self.name, success=False, result="",
                error="duckduckgo-search not installed. Run: pip install duckduckgo-search",
            )

        try:
            with DDGS() as ddgs:
                if search_type == "news":
                    results = list(ddgs.news(query, max_results=max_results))
                else:
                    results = list(ddgs.text(query, max_results=max_results))

            formatted = json.dumps(results, ensure_ascii=False, indent=2)
            summary = "\n".join(
                f"- [{r.get('title', 'N/A')}]({r.get('href', r.get('url', ''))}) — {r.get('body', r.get('excerpt', ''))[:100]}"
                for r in results
            )

            return SkillResult(
                skill=self.name, success=True,
                result=summary,
                metadata={"query": query, "count": len(results), "raw": results},
            )
        except Exception as e:
            return SkillResult(skill=self.name, success=False, result="", error=str(e))
