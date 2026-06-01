from backend.browser.profile_manager import BrowserProfileManager
from .base_web_ai_adapter import BaseWebAIAdapter
from .login_detector import LoginDetector
from .prompt_sender import PromptSender
from .answer_extractor import AnswerExtractor
from .selectors import URLS


class ClaudeWebAdapter(BaseWebAIAdapter):
    provider_name = "claude"
    url = URLS["claude"]

    def __init__(self, page=None, profile_name: str = "claude", headless: bool = False, debug: bool = False):
        super().__init__(page)
        self.profile_name = profile_name
        self.headless = headless
        self.debug = debug
        self.manager = BrowserProfileManager()
        self.login_detector = LoginDetector()
        self.sender = PromptSender()
        self.extractor = AnswerExtractor()

    async def open(self) -> None:
        if self.page is None:
            self.page = await self.manager.new_page(self.profile_name, self.headless)
        await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
        await self._dismiss_nonessential_popups()
        try:
            new_chat = self.page.locator("button:has-text('New chat'), a:has-text('New chat')").first
            if await new_chat.count():
                await new_chat.click(timeout=5000)
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        await self._dismiss_nonessential_popups()
        try:
            await self.page.locator(
                "div[contenteditable='true'], textarea, div.ProseMirror"
            ).last.wait_for(state="visible", timeout=15000)
        except Exception:
            pass

    async def _dismiss_nonessential_popups(self) -> None:
        for selector in [
            "button[aria-label='Close']",
            "button[aria-label*='close' i]",
            "button:has-text('×')",
            "button:has-text('Got it')",
            "button:has-text('Not now')",
        ]:
            try:
                button = self.page.locator(selector).last
                if await button.count():
                    await button.click(timeout=3000, force=True)
                    await self.page.wait_for_timeout(500)
            except Exception:
                continue

    async def is_logged_in(self) -> bool:
        return await self.login_detector.detect(self.page, self.provider_name)

    async def send_prompt(
        self, prompt: str, attachments: list[str] | None = None
    ) -> None:
        return await self.sender.send(self.page, self.provider_name, prompt, attachments, self.debug)

    async def wait_for_answer_complete(self, timeout: int = 180) -> bool:
        return await self.extractor.wait_complete(self.page, timeout)

    async def extract_latest_answer(self, prompt: str = "") -> str:
        return await self.extractor.latest(self.page, self.provider_name, prompt)
