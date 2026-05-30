"""Browser Skill — Web automation via Playwright or fallback."""

from __future__ import annotations
import json
from .base import Skill, SkillResult, RiskLevel


class BrowserSkill(Skill):
    name = "browser"
    description = "Control web browser for navigation, extraction, and interaction"
    capabilities = [
        "open_url",
        "extract_page_text",
        "screenshot_page",
        "click_element",
        "fill_form",
        "search_web",
    ]
    risk_level = RiskLevel.LOW

    def __init__(self):
        self._browser = None
        self._page = None

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["browser", "web", "url", "page", "website", "navigate", "search"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def _ensure_browser(self):
        """Lazily launch browser."""
        if self._page is not None:
            return
        try:
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            self._page = await self._browser.new_page()
        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "open_url")

        try:
            await self._ensure_browser()

            if action == "open_url":
                return await self._open_url(context.get("url", ""))
            elif action == "extract_page_text":
                return await self._extract_text()
            elif action == "screenshot_page":
                return await self._screenshot(context.get("save_as", "screenshot.png"))
            elif action == "click_element":
                return await self._click(context.get("selector", ""))
            elif action == "fill_form":
                return await self._fill(
                    context.get("selector", ""), context.get("value", "")
                )
            elif action == "search_web":
                return await self._search(context.get("query", instruction))
            else:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(skill=self.name, success=False, result="", error=str(e))

    async def _open_url(self, url: str) -> SkillResult:
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        title = await self._page.title()
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Opened: {url} — Title: {title}",
            metadata={"url": url, "title": title},
        )

    async def _extract_text(self) -> SkillResult:
        text = await self._page.inner_text("body")
        return SkillResult(
            skill=self.name,
            success=True,
            result=text[:5000],
            metadata={"length": len(text)},
        )

    async def _screenshot(self, save_as: str) -> SkillResult:
        await self._page.screenshot(path=save_as, full_page=True)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Screenshot saved: {save_as}",
            evidence=[save_as],
        )

    async def _click(self, selector: str) -> SkillResult:
        await self._page.click(selector, timeout=10000)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Clicked: {selector}",
        )

    async def _fill(self, selector: str, value: str) -> SkillResult:
        await self._page.fill(selector, value, timeout=10000)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Filled {selector} with value",
        )

    async def _search(self, query: str) -> SkillResult:
        """Search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            formatted = json.dumps(results, ensure_ascii=False, indent=2)
            return SkillResult(
                skill=self.name,
                success=True,
                result=formatted,
                metadata={"query": query, "count": len(results)},
            )
        except Exception as e:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Search failed: {e}",
            )
