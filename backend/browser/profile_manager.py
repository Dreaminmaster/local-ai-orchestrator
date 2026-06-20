"""Persistent Playwright browser profiles for login-state reuse."""

from pathlib import Path
from typing import Any


class BrowserProfileManager:
    def __init__(self, base_dir: str = "runtime/browser_profiles"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = None
        self.contexts: dict[str, Any] = {}
        self.last_launch_details: dict[str, dict] = {}

    async def start(self):
        if self.playwright is None:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

    async def get_context(self, profile_name: str, headless: bool = False):
        await self.start()
        if profile_name in self.contexts:
            return self.contexts[profile_name]
        profile_dir = self.base_dir / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        details = {
            "profile_dir": str(profile_dir.resolve()),
            "headless": headless,
            "browser_started": False,
            "page_created": False,
            "visible_window_expected": not headless,
        }
        self.last_launch_details[profile_name] = details
        try:
            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir.resolve()),
                headless=headless,
                viewport={"width": 1440, "height": 1000},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
            )
        except Exception as exc:
            details["failure_reason"] = str(exc)
            raise
        details["browser_started"] = True
        self.contexts[profile_name] = context
        return context

    async def new_page(self, profile_name: str, headless: bool = False):
        context = await self.get_context(profile_name, headless=headless)
        page = context.pages[0] if context.pages else await context.new_page()
        self.last_launch_details.setdefault(profile_name, {})["page_created"] = True
        try:
            await page.bring_to_front()
        except Exception as exc:
            self.last_launch_details[profile_name]["bring_to_front_error"] = str(exc)
        return page

    async def close_context(self, profile_name: str):
        context = self.contexts.pop(profile_name, None)
        if context is not None:
            await context.close()

    async def close_all(self):
        for ctx in list(self.contexts.values()):
            await ctx.close()
        self.contexts.clear()
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
