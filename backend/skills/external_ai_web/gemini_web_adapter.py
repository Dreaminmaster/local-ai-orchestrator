from .base_web_ai_adapter import BaseWebAIAdapter
from .login_detector import LoginDetector
from .prompt_sender import PromptSender
from .answer_extractor import AnswerExtractor
from .selectors import URLS


class GeminiWebAdapter(BaseWebAIAdapter):
    provider_name = "gemini"
    url = URLS["gemini"]

    def __init__(
        self, page=None, profile_name: str = "gemini", headless: bool = False, debug: bool = False
    ):
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
        await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)

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
