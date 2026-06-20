"""Persistent browser workspace manager for external AI providers."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.browser.profile_manager import BrowserProfileManager
from backend.runtime_paths import resolve_runtime_paths

from .login_detector import LoginDetector
from .provider_status import ProviderState, normalize_provider, profile_dir
from .selectors import SELECTORS, URLS


STALE_CONVERSATION_MARKERS = [
    "this conversation could not be found",
    "conversation not found",
    "chat not found",
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


class ProfileInUseByBackend(RuntimeError):
    """Raised before Chromium launch when another backend owns a profile."""

    code = "PROFILE_IN_USE_BY_BACKEND"


@dataclass
class WorkspaceStatus:
    provider: str
    state: ProviderState
    profile_dir: str
    page_url: str = ""
    opened_at: str = ""
    last_error: str = ""
    need_user_intervention: bool = False
    owner_pid: int | None = None
    owner_type: str = ""
    app_instance_id: str = ""
    last_activity_at: str = ""
    active_request_id: str = ""
    workspace_reused: bool = False
    second_context_created: bool = False
    request_id: str = ""
    browser_started: bool = False
    page_created: bool = False
    visible_window_expected: bool = False
    failure_code: str = ""
    failure_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "state": self.state.value,
            "profile_dir": self.profile_dir,
            "page_url": self.page_url,
            "opened_at": self.opened_at,
            "last_error": self.last_error,
            "need_user_intervention": self.need_user_intervention,
            "owner_pid": self.owner_pid,
            "owner_type": self.owner_type,
            "app_instance_id": self.app_instance_id,
            "last_activity_at": self.last_activity_at,
            "active_request_id": self.active_request_id,
            "workspace_reused": self.workspace_reused,
            "second_context_created": self.second_context_created,
            "request_id": self.request_id,
            "workspace_state": self.state.value,
            "browser_started": self.browser_started,
            "page_created": self.page_created,
            "visible_window_expected": self.visible_window_expected,
            "current_url": self.page_url,
            "failure_code": self.failure_code,
            "failure_reason": self.failure_reason,
        }


class ExternalAIWorkspaceManager:
    """Keep one project-local persistent browser workspace per provider."""

    def __init__(
        self, base_dir: str | None = None, owner_type: str = "backend"
    ):
        if base_dir is None:
            base_dir = str(resolve_runtime_paths().ensure().browser_profiles_dir)
        self.browser = BrowserProfileManager(base_dir=base_dir)
        self.login_detector = LoginDetector()
        self.owner_type = owner_type
        self.app_instance_id = uuid.uuid4().hex
        self.owner_pid = os.getpid()
        self.pages: dict[str, Any] = {}
        self.opened_at: dict[str, str] = {}
        self.last_activity_at: dict[str, str] = {}
        self.last_errors: dict[str, str] = {}
        self.last_statuses: dict[str, WorkspaceStatus] = {}
        self.last_recoveries: dict[str, dict] = {}
        self.active_request_ids: dict[str, str] = {}
        self.request_locks: dict[str, asyncio.Lock] = {}
        self.lifecycle_locks: dict[str, asyncio.Lock] = {}
        self.workspace_reused: dict[str, bool] = {}
        self.open_request_ids: dict[str, str] = {}
        self.last_failure_codes: dict[str, str] = {}
        self.opening_providers: set[str] = set()
        self.last_exchanges: dict[str, dict] = {}

    def configure_runtime_paths(self) -> Path:
        """Bind profile storage to the final backend runtime environment."""
        if self.pages or self.browser.contexts:
            raise RuntimeError("cannot_reconfigure_workspace_paths_while_open")
        target = resolve_runtime_paths().ensure().browser_profiles_dir.resolve()
        self.browser.base_dir = target
        self.browser.base_dir.mkdir(parents=True, exist_ok=True)
        return target

    def _request_lock(self, provider: str) -> asyncio.Lock:
        return self.request_locks.setdefault(provider, asyncio.Lock())

    def _lifecycle_lock(self, provider: str) -> asyncio.Lock:
        return self.lifecycle_locks.setdefault(provider, asyncio.Lock())

    def _owner_path(self, provider: str) -> Path:
        return profile_dir(provider, self.browser.base_dir) / ".workspace-owner.json"

    def _owner_payload(self, provider: str) -> dict:
        return {
            "provider": provider,
            "owner_pid": self.owner_pid,
            "owner_type": self.owner_type,
            "started_at": self.opened_at.get(provider, datetime.now().isoformat()),
            "profile_dir": str(profile_dir(provider, self.browser.base_dir)),
            "app_instance_id": self.app_instance_id,
        }

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (OSError, TypeError, ValueError):
            return False

    def inspect_owner(self, provider: str) -> dict:
        provider = normalize_provider(provider)
        path = self._owner_path(provider)
        if not path.exists():
            return {}
        try:
            owner = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            owner = {}
        owner["owner_file"] = str(path)
        owner["stale"] = not self._pid_alive(owner.get("owner_pid"))
        return owner

    def _claim_owner(self, provider: str) -> None:
        provider = normalize_provider(provider)
        path = self._owner_path(provider)
        path.parent.mkdir(parents=True, exist_ok=True)
        owner = self.inspect_owner(provider)
        if owner and not owner.get("stale"):
            same_owner = (
                owner.get("owner_pid") == self.owner_pid
                and owner.get("app_instance_id") == self.app_instance_id
            )
            if not same_owner:
                raise ProfileInUseByBackend(
                    f"{ProfileInUseByBackend.code}: provider={provider} "
                    f"owner_pid={owner.get('owner_pid')}"
                )
        elif owner:
            path.unlink(missing_ok=True)
        path.write_text(
            json.dumps(self._owner_payload(provider), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _release_owner(self, provider: str) -> None:
        path = self._owner_path(provider)
        owner = self.inspect_owner(provider)
        if (
            owner.get("owner_pid") == self.owner_pid
            and owner.get("app_instance_id") == self.app_instance_id
        ):
            path.unlink(missing_ok=True)

    async def open_workspace(self, provider: str):
        provider = normalize_provider(provider)
        if self.owner_type != "backend":
            raise RuntimeError("WORKSPACE_ACCESS_REQUIRES_BACKEND_API")
        existing = await self.reuse_existing_page(provider)
        if existing is not None:
            self.workspace_reused[provider] = True
            self.last_activity_at[provider] = datetime.now().isoformat()
            try:
                await existing.bring_to_front()
            except Exception:
                pass
            return existing
        async with self._lifecycle_lock(provider):
            existing = await self.reuse_existing_page(provider)
            if existing is not None:
                self.workspace_reused[provider] = True
                return existing
            self.opening_providers.add(provider)
            self.last_statuses[provider] = self._status(
                provider, ProviderState.OPENING
            )
            try:
                self._claim_owner(provider)
                if provider in self.browser.contexts:
                    await self.browser.close_context(provider)
                page = await self.browser.new_page(provider, headless=False)
            except Exception as exc:
                message = str(exc)
                self.last_errors[provider] = message
                self.last_failure_codes[provider] = (
                    "PROJECT_BROWSER_MISSING"
                    if "Executable doesn't exist" in message
                    or "playwright install" in message.lower()
                    else "BROWSER_WINDOW_CREATE_FAILED"
                )
                self._release_owner(provider)
                self.opening_providers.discard(provider)
                raise
            try:
                self.pages[provider] = page
                self.workspace_reused[provider] = False
                self.opened_at.setdefault(provider, datetime.now().isoformat())
                self.last_activity_at[provider] = datetime.now().isoformat()
                url = URLS.get(provider)
                if url and not page.url.startswith("http"):
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    except Exception as exc:
                        self.last_errors[provider] = str(exc)
                        self.last_failure_codes[provider] = "PROVIDER_PAGE_OPEN_FAILED"
                        raise
                try:
                    await page.bring_to_front()
                except Exception:
                    pass
                return page
            finally:
                self.opening_providers.discard(provider)

    async def ensure_workspace(self, provider: str):
        provider = normalize_provider(provider)
        page = await self.reuse_existing_page(provider)
        if page is not None:
            self.workspace_reused[provider] = True
            self.last_activity_at[provider] = datetime.now().isoformat()
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
        context = self.browser.contexts.get(provider)
        if context is not None and hasattr(context, "pages"):
            candidates = []
            for candidate in context.pages:
                try:
                    if not candidate.is_closed():
                        candidates.append(candidate)
                except Exception:
                    continue
            provider_pages = [
                candidate
                for candidate in candidates
                if provider in (getattr(candidate, "url", "") or "").lower()
                or (
                    provider == "claude"
                    and "claude.ai" in (getattr(candidate, "url", "") or "").lower()
                )
            ]
            if provider_pages and page not in provider_pages:
                page = provider_pages[-1]
                self.pages[provider] = page
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
        async with self._lifecycle_lock(provider):
            self.pages.pop(provider, None)
            try:
                await self.browser.close_context(provider)
            except Exception as exc:
                self.last_errors[provider] = str(exc)
            self._release_owner(provider)
            self.active_request_ids.pop(provider, None)
        return await self.get_workspace_status(provider)

    def record_exchange(
        self,
        provider: str,
        *,
        prompt: str,
        answer: str,
        quality: dict | None = None,
        evidence_path: str = "",
        selector: str = "",
        warning_text: str = "",
        warning_class: str = "",
        task_id: str = "",
        step_id: str = "",
    ) -> None:
        provider = normalize_provider(provider)
        self.last_exchanges[provider] = {
            "provider": provider,
            "task_id": task_id,
            "step_id": step_id,
            "last_prompt": prompt,
            "last_answer": answer,
            "last_answer_preview": (answer or "")[:500],
            "quality_result": quality or {},
            "answer_selector": selector,
            "warning_text": warning_text,
            "warning_class": warning_class,
            "evidence_path": evidence_path,
            "updated_at": datetime.now().isoformat(),
        }

    async def workspace_console(self) -> dict:
        providers = ["claude", "chatgpt", "gemini", "kimi", "doubao"]
        statuses = {}
        for provider in providers:
            status = await self.get_workspace_status(provider)
            statuses[provider] = {
                **status.to_dict(),
                "exchange": self.last_exchanges.get(provider, {}),
            }
        return {
            "providers": statuses,
            "enabled_count": len(providers),
            "logged_in_count": sum(
                1 for item in statuses.values()
                if item.get("workspace_state") in {"READY", "PASS", "PARTIAL", "BUSY"}
            ),
            "route_ready_count": sum(
                1 for item in statuses.values()
                if (item.get("exchange", {}).get("quality_result") or {}).get("quality")
                in {"PASS", "PASS_WITH_WARNING"}
            ),
            "active_provider": next(
                (
                    name for name, item in statuses.items()
                    if item.get("active_request_id")
                ),
                "",
            ),
        }

    async def shutdown(self) -> None:
        providers = set(self.pages) | set(self.browser.contexts)
        for provider in list(providers):
            await self.close_workspace(provider)
        await self.browser.close_all()

    @asynccontextmanager
    async def provider_request(self, provider: str, request_id: str = ""):
        provider = normalize_provider(provider)
        request_id = request_id or uuid.uuid4().hex
        lock = self._request_lock(provider)
        await lock.acquire()
        self.active_request_ids[provider] = request_id
        self.last_activity_at[provider] = datetime.now().isoformat()
        try:
            yield request_id
        finally:
            self.last_activity_at[provider] = datetime.now().isoformat()
            self.active_request_ids.pop(provider, None)
            lock.release()

    def _status(
        self,
        provider: str,
        state: ProviderState,
        *,
        page: Any = None,
        last_error: str = "",
        need_user_intervention: bool = False,
    ) -> WorkspaceStatus:
        owner = self.inspect_owner(provider)
        launch = getattr(self.browser, "last_launch_details", {}).get(provider, {})
        failure_reason = last_error or self.last_errors.get(provider, "")
        return WorkspaceStatus(
            provider=provider,
            state=state,
            profile_dir=str(profile_dir(provider, self.browser.base_dir)),
            page_url=getattr(page, "url", "") if page is not None else "",
            opened_at=self.opened_at.get(provider, ""),
            last_error=last_error,
            need_user_intervention=need_user_intervention,
            owner_pid=owner.get("owner_pid"),
            owner_type=owner.get("owner_type", ""),
            app_instance_id=owner.get("app_instance_id", ""),
            last_activity_at=self.last_activity_at.get(provider, ""),
            active_request_id=self.active_request_ids.get(provider, ""),
            workspace_reused=self.workspace_reused.get(provider, False),
            second_context_created=False,
            request_id=self.open_request_ids.get(provider, ""),
            browser_started=bool(launch.get("browser_started")),
            page_created=bool(launch.get("page_created")),
            visible_window_expected=bool(launch.get("visible_window_expected")),
            failure_code=self.last_failure_codes.get(provider, ""),
            failure_reason=failure_reason,
        )

    async def get_workspace_status(self, provider: str) -> WorkspaceStatus:
        provider = normalize_provider(provider)
        pdir = profile_dir(provider, self.browser.base_dir)
        page = await self.reuse_existing_page(provider)
        if provider in self.opening_providers:
            status = self._status(provider, ProviderState.OPENING)
            self.last_statuses[provider] = status
            return status
        if not pdir.exists() or not any(pdir.iterdir()):
            status = self._status(
                provider,
                ProviderState.NOT_CONFIGURED,
                last_error=self.last_errors.get(provider, ""),
            )
            self.last_statuses[provider] = status
            return status
        if page is None:
            owner = self.inspect_owner(provider)
            state = (
                ProviderState.CRASHED
                if owner and not owner.get("stale")
                else ProviderState.CLOSED
            )
            status = self._status(
                provider,
                state,
                last_error=self.last_errors.get(
                    provider, "workspace_not_open_login_state_unverified"
                ),
                need_user_intervention=True,
            )
            self.last_statuses[provider] = status
            return status
        try:
            state = await self.detect_page_state(page, provider)
            if self._request_lock(provider).locked() and state == ProviderState.READY:
                state = ProviderState.BUSY
            status = self._status(
                provider,
                state,
                page=page,
                last_error=self.last_errors.get(provider, ""),
                need_user_intervention=state
                in {
                    ProviderState.NEED_LOGIN,
                    ProviderState.NEED_USER_INTERVENTION,
                    ProviderState.STALE_CONVERSATION,
                    ProviderState.PAGE_NETWORK_ERROR,
                    ProviderState.RETRYABLE_PAGE_ERROR,
                    ProviderState.CRASHED,
                    ProviderState.PAGE_ERROR,
                    ProviderState.UNKNOWN_ERROR,
                },
            )
            self.last_statuses[provider] = status
            return status
        except Exception as exc:
            self.last_errors[provider] = str(exc)
            status = self._status(
                provider,
                ProviderState.CRASHED,
                page=page,
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
        input_visible = await self._input_visible(page, provider)

        if any(marker in lowered for marker in NEED_USER_INTERVENTION_MARKERS):
            return ProviderState.NEED_USER_INTERVENTION
        if provider == "claude" and any(
            marker in lowered for marker in STALE_CONVERSATION_MARKERS
        ) and not input_visible:
            return ProviderState.STALE_CONVERSATION
        if any(marker in lowered for marker in PAGE_NETWORK_ERROR_MARKERS):
            return ProviderState.PAGE_NETWORK_ERROR
        if any(marker in url for marker in ["login", "signin", "auth"]):
            return ProviderState.NEED_LOGIN
        if any(marker in lowered[:4000] for marker in LOGIN_MARKERS):
            return ProviderState.NEED_LOGIN
        if input_visible:
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


workspace_manager = ExternalAIWorkspaceManager(
    owner_type=os.environ.get("LOCAL_AI_WORKSPACE_OWNER_TYPE", "process")
)
