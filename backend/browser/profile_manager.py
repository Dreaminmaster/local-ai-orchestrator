"""Persistent Playwright browser profiles for login-state reuse."""
from pathlib import Path
from typing import Any


class BrowserProfileManager:
    def __init__(self, base_dir: str = "runtime/browser_profiles"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = None
        self.contexts: dict[str, Any] = {}

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
        context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            viewport={"width": 1440, "height": 1000},
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
        )
        self.contexts[profile_name] = context
        return context

    async def new_page(self, profile_name: str, headless: bool = False):
        context = await self.get_context(profile_name, headless=headless)
        if context.pages:
            return context.pages[0]
        return await context.new_page()

    async def close_all(self):
        for ctx in self.contexts.values():
            await ctx.close()
        self.contexts.clear()
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
