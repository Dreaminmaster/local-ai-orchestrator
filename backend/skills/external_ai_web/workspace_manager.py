"""Persistent browser workspace manager for external AI providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.browser.profile_manager import BrowserProfileManager

from .login_detector import LoginDetector
from .provider_status import ProviderState, normalize_provider, profile_dir
from .selectors import SELECTORS, URLS


STALE_CONVERSATION_MARKERS = [
    "this conversation could not be found",
    "conversation not found",
    "chat not found",
    "unavailable",
    "not found",
]

PAGE_NETWORK_ERROR_MARKERS = [
    "network error",
    "connection lost",
    "connection failed",
    "unable to connect",
    "request timed out",
    "reconnecting",
    "网络错误",
    "无法连接",
    "连接失败",
    "请求超时",
]

NEED_USER_INTERVENTION_MARKERS = [
    "captcha",
    "cloudflare",
    "verify you are human",
    "human verification",
    "security challenge",
    "验证码",
    "人机验证",
    "安全验证",
    "请验证你是真人",
]

LOGIN_MARKERS = [
    "sign in",
    "log in",
    "login",
    "continue with google",
    "continue with apple",
    "continue with email",
    "session expired",
    "please log in again",
    "please sign in again",
    "登录",
    "注册",
    "继续使用",
]


@dataclass
class WorkspaceStatus:
    provider: str
    state: ProviderState
    profile_dir: str
    page_url: str = ""
    opened_at: str = ""
    last_error: str = ""
    need_user_intervention: bool = False

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "state": self.state.value,
            "profile_dir": self.profile_dir,
            "page_url": self.page_url,
            "opened_at": self.opened_at,
            "last_error": self.last_error,
            "need_user_intervention": self.need_user_intervention,
        }


class ExternalAIWorkspaceManager:
    """Keep one project-local persistent browser workspace per provider."""

    def __init__(self, base_dir: str = "runtime/browser_profiles"):
        self.browser = BrowserProfileManager(base_dir=base_dir)
        self.login_detector = LoginDetector()
        self.pages: dict[str, Any] = {}
        self.opened_at: dict[str, str] = {}
        self.last_errors: dict[str, str] = {}
        self.last_statuses: dict[str, WorkspaceStatus] = {}
        self.last_recoveries: dict[str, dict] = {}

    async def open_workspace(self, provider: str):
        provider = normalize_provider(provider)
        page = await self.browser.new_page(provider, headless=False)
        self.pages[provider] = page
        self.opened_at.setdefault(provider, datetime.now().isoformat())
        url = URLS.get(provider)
        if url and not page.url.startswith("http"):
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        return page

    async def ensure_workspace(self, provider: str):
        provider = normalize_provider(provider)
        page = await self.reuse_existing_page(provider)
        if page is not None:
            status = await self.get_workspace_status(provider)
            if status.state == ProviderState.STALE_CONVERSATION:
                await self.recover_workspace(provider, "stale_conversation")
            return page
        page = await self.open_workspace(provider)
        status = await self.get_workspace_status(provider)
        if status.state == ProviderState.STALE_CONVERSATION:
            await self.recover_workspace(provider, "stale_conversation")
        return page

    async def reuse_existing_page(self, provider: str):
        provider = normalize_provider(provider)
        page = self.pages.get(provider)
        if page is None:
            return None
        try:
            if page.is_closed():
                self.pages.pop(provider, None)
                return None
        except Exception:
            self.pages.pop(provider, None)
            return None
        return page

    async def close_workspace(self, provider: str) -> WorkspaceStatus:
        provider = normalize_provider(provider)
        page = self.pages.pop(provider, None)
        try:
            if page is not None and not page.is_closed():
                await page.close()
        except Exception as exc:
            self.last_errors[provider] = str(exc)
        return await self.get_workspace_status(provider)

    async def get_workspace_status(self, provider: str) -> WorkspaceStatus:
        provider = normalize_provider(provider)
        pdir = profile_dir(provider, self.browser.base_dir)
        page = await self.reuse_existing_page(provider)
        if not pdir.exists() or not any(pdir.iterdir()):
            status = WorkspaceStatus(
                provider=provider,
                state=ProviderState.NOT_CONFIGURED,
                profile_dir=str(pdir),
                last_error=self.last_errors.get(provider, ""),
            )
            self.last_statuses[provider] = status
            return status
        if page is None:
            status = WorkspaceStatus(
                provider=provider,
                state=ProviderState.READY,
                profile_dir=str(pdir),
                last_error=self.last_errors.get(provider, ""),
            )
            self.last_statuses[provider] = status
            return status
        try:
            state = await self.detect_page_state(page, provider)
            status = WorkspaceStatus(
                provider=provider,
                state=state,
                profile_dir=str(pdir),
                page_url=page.url,
                opened_at=self.opened_at.get(provider, ""),
                last_error=self.last_errors.get(provider, ""),
                need_user_intervention=state == ProviderState.NEED_USER_INTERVENTION,
            )
            self.last_statuses[provider] = status
            return status
        except Exception as exc:
            self.last_errors[provider] = str(exc)
            status = WorkspaceStatus(
                provider=provider,
                state=ProviderState.UNKNOWN_ERROR,
                profile_dir=str(pdir),
                page_url=getattr(page, "url", ""),
                opened_at=self.opened_at.get(provider, ""),
                last_error=str(exc),
                need_user_intervention=True,
            )
            self.last_statuses[provider] = status
            return status

    async def detect_page_state(self, page, provider: str) -> ProviderState:
        provider = normalize_provider(provider)
        try:
            if page is None or page.is_closed():
                return ProviderState.CLOSED
        except Exception:
            return ProviderState.CLOSED

        url = (getattr(page, "url", "") or "").lower()
        text = await self._body_text(page)
        lowered = text.lower()

        if any(marker in lowered for marker in NEED_USER_INTERVENTION_MARKERS):
            return ProviderState.NEED_USER_INTERVENTION
        if provider == "claude" and any(
            marker in lowered for marker in STALE_CONVERSATION_MARKERS
        ):
            return ProviderState.STALE_CONVERSATION
        if any(marker in lowered for marker in PAGE_NETWORK_ERROR_MARKERS):
            return ProviderState.PAGE_NETWORK_ERROR
        if any(marker in url for marker in ["login", "signin", "auth"]):
            return ProviderState.NEED_LOGIN
        if any(marker in lowered[:4000] for marker in LOGIN_MARKERS):
            return ProviderState.NEED_LOGIN
        if await self._input_visible(page, provider):
            return ProviderState.READY
        return ProviderState.OPEN

    async def recover_workspace(self, provider: str, reason: str) -> dict:
        provider = normalize_provider(provider)
        page = await self.reuse_existing_page(provider)
        before_url = getattr(page, "url", "") if page is not None else ""
        recovery = {
            "recovered": False,
            "reason": reason,
            "action_taken": "",
            "before_url": before_url,
            "after_url": before_url,
            "status_after_recovery": "",
        }
        if page is None:
            recovery["action_taken"] = "no_open_page"
            recovery["status_after_recovery"] = ProviderState.CLOSED.value
            self.last_recoveries[provider] = recovery
            return recovery
        if provider != "claude" or reason != "stale_conversation":
            recovery["action_taken"] = "no_recovery_available"
            self.last_recoveries[provider] = recovery
            return recovery
        try:
            recovery["action_taken"] = "navigate_to_new_conversation"
            await page.goto(URLS["claude"], wait_until="domcontentloaded", timeout=60000)
            await self._wait_for_input(page, provider, timeout=20000)
            status = await self.get_workspace_status(provider)
            recovery["after_url"] = getattr(page, "url", "")
            recovery["status_after_recovery"] = status.state.value
            recovery["recovered"] = status.state == ProviderState.READY
        except Exception as exc:
            self.last_errors[provider] = str(exc)
            recovery["after_url"] = getattr(page, "url", "")
            recovery["status_after_recovery"] = ProviderState.NEED_USER_INTERVENTION.value
            recovery["error"] = str(exc)
            self.last_statuses[provider] = WorkspaceStatus(
                provider=provider,
                state=ProviderState.NEED_USER_INTERVENTION,
                profile_dir=str(profile_dir(provider, self.browser.base_dir)),
                page_url=recovery["after_url"],
                opened_at=self.opened_at.get(provider, ""),
                last_error=str(exc),
                need_user_intervention=True,
            )
        self.last_recoveries[provider] = recovery
        return recovery

    async def _body_text(self, page) -> str:
        try:
            return await page.locator("body").inner_text(timeout=2000)
        except Exception:
            return ""

    async def _input_visible(self, page, provider: str) -> bool:
        selector = SELECTORS.get(provider, {}).get(
            "input", "textarea, [contenteditable='true'], [role='textbox']"
        )
        try:
            locator = page.locator(selector).last
            if not await locator.count():
                return False
            return await locator.is_visible(timeout=2000)
        except TypeError:
            try:
                return await locator.is_visible()
            except Exception:
                return False
        except Exception:
            return False

    async def _wait_for_input(self, page, provider: str, timeout: int) -> None:
        selector = SELECTORS.get(provider, {}).get(
            "input", "textarea, [contenteditable='true'], [role='textbox']"
        )
        await page.locator(selector).last.wait_for(state="visible", timeout=timeout)


workspace_manager = ExternalAIWorkspaceManager()
