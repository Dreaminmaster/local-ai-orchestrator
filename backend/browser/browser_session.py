"""High-level persistent browser session."""

from dataclasses import dataclass
from .profile_manager import BrowserProfileManager


@dataclass
class BrowserSessionState:
    profile: str
    url: str
    title: str
    logged_in_hint: bool | None = None


class BrowserSession:
    def __init__(self, profile_name: str = "default", headless: bool = False):
        self.profile_name = profile_name
        self.headless = headless
        self.manager = BrowserProfileManager()
        self.page = None

    async def open(self, url: str):
        self.page = await self.manager.new_page(self.profile_name, self.headless)
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        return await self.state()

    async def state(self) -> BrowserSessionState:
        if not self.page:
            return BrowserSessionState(self.profile_name, "", "")
        return BrowserSessionState(
            self.profile_name, self.page.url, await self.page.title()
        )

    async def screenshot(self, path: str, full_page: bool = True):
        await self.page.screenshot(path=path, full_page=full_page)
        return path
