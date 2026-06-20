from .base_web_ai_adapter import BaseWebAIAdapter
from .login_detector import LoginDetector
from .prompt_sender import PromptSender
from .answer_extractor import AnswerExtractor
from .selectors import URLS
from .provider_status import ProviderState
from .workspace_manager import workspace_manager


class ClaudeWebAdapter(BaseWebAIAdapter):
    provider_name = "claude"
    url = URLS["claude"]

    def __init__(self, page=None, profile_name: str = "claude", headless: bool = False, debug: bool = False):
        super().__init__(page)
        self.profile_name = profile_name
        self.headless = headless
        self.debug = debug
        self.login_detector = LoginDetector()
        self.sender = PromptSender()
        self.extractor = AnswerExtractor()

    async def open(self) -> None:
        if self.page is None:
            raise RuntimeError("WORKSPACE_REQUIRED_BACKEND_SINGLE_OWNER")
        current_url = (getattr(self.page, "url", "") or "").lower()
        if "claude.ai" not in current_url:
            await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
        await self._dismiss_nonessential_popups()
        try:
            await self.page.locator(
                "div[contenteditable='true'], textarea, div.ProseMirror, [role='textbox']"
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
        state = await workspace_manager.detect_page_state(self.page, self.provider_name)
        return state == ProviderState.READY

    async def send_prompt(
        self, prompt: str, attachments: list[str] | None = None
    ) -> None:
        return await self.sender.send(self.page, self.provider_name, prompt, attachments, self.debug)

    async def wait_for_answer_complete(self, timeout: int = 180) -> bool:
        return await self.extractor.wait_complete(self.page, timeout)

    async def extract_latest_answer(self, prompt: str = "") -> str:
        return await self.extractor.latest(self.page, self.provider_name, prompt)
