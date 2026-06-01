from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class WebAIMessage:
    role: str
    content: str
    timestamp: str | None = None


@dataclass
class WebAIResponse:
    provider: str
    success: bool
    answer: str
    messages: List[WebAIMessage] = field(default_factory=list)
    evidence_files: List[str] = field(default_factory=list)
    error: Optional[str] = None
    needs_login: bool = False
    needs_follow_up: bool = False
    metadata: Dict[str, Any] | None = None


class BaseWebAIAdapter(ABC):
    provider_name: str = "base"
    url: str = ""

    def __init__(self, page=None):
        self.page = page

    @abstractmethod
    async def open(self) -> None: ...

    @abstractmethod
    async def is_logged_in(self) -> bool: ...

    @abstractmethod
    async def send_prompt(
        self, prompt: str, attachments: list[str] | None = None
    ) -> None: ...

    @abstractmethod
    async def wait_for_answer_complete(self, timeout: int = 180) -> bool: ...

    @abstractmethod
    async def extract_latest_answer(self, prompt: str = "") -> str: ...

    async def ask(
        self, prompt: str, attachments: list[str] | None = None
    ) -> WebAIResponse:
        await self.open()
        if not await self.is_logged_in():
            shot = f"runtime/evidence/{self.provider_name}_needs_login.png"
            try:
                await self.page.screenshot(path=shot, full_page=True)
                evidence = [shot]
            except Exception:
                evidence = []
            return WebAIResponse(
                self.provider_name, False, "", [], evidence, "login required", True
            )
        send_meta = await self.send_prompt(prompt, attachments)
        complete = await self.wait_for_answer_complete()
        answer = await self.extract_latest_answer(prompt) if complete else ""
        extract_meta = {
            "complete": complete,
            "used_selector": getattr(getattr(self, "extractor", None), "used_selector", ""),
            "body_fallback": getattr(getattr(self, "extractor", None), "used_body_fallback", False),
            "raw_body_fallback": getattr(getattr(self, "extractor", None), "raw_body_fallback", ""),
            "error_reason": getattr(getattr(self, "extractor", None), "error_reason", ""),
            "candidate_selectors": getattr(
                getattr(self, "extractor", None), "candidate_selectors", []
            ),
        }
        return WebAIResponse(
            provider=self.provider_name,
            success=bool(answer),
            answer=answer,
            messages=[
                WebAIMessage("user", prompt, datetime.now().isoformat()),
                WebAIMessage("assistant", answer, datetime.now().isoformat()),
            ],
            evidence_files=[],
            needs_follow_up=len(answer.strip()) < 80,
            metadata={
                "complete": complete,
                "send": send_meta or {},
                "extract": extract_meta,
            },
        )
