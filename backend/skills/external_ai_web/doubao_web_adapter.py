from backend.browser.profile_manager import BrowserProfileManager
from .base_web_ai_adapter import BaseWebAIAdapter
from .login_detector import LoginDetector
from .prompt_sender import PromptSender
from .answer_extractor import AnswerExtractor
from .selectors import URLS


class DoubaoWebAdapter(BaseWebAIAdapter):
    provider_name = "doubao"
    url = URLS["doubao"]

    def __init__(self, page=None, profile_name: str = "doubao", headless: bool = False):
        super().__init__(page)
        self.profile_name = profile_name
        self.headless = headless
        self.manager = BrowserProfileManager()
        self.login_detector = LoginDetector()
        self.sender = PromptSender()
        self.extractor = AnswerExtractor()

    async def open(self) -> None:
        if self.page is None:
            self.page = await self.manager.new_page(self.profile_name, self.headless)
        await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)

    async def is_logged_in(self) -> bool:
        return await self.login_detector.detect(self.page, self.provider_name)

    async def send_prompt(
        self, prompt: str, attachments: list[str] | None = None
    ) -> None:
        await self.sender.send(self.page, self.provider_name, prompt, attachments)

    async def wait_for_answer_complete(self, timeout: int = 180) -> bool:
        return await self.extractor.wait_complete(self.page, timeout)

    async def extract_latest_answer(self) -> str:
        return await self.extractor.latest(self.page, self.provider_name)
