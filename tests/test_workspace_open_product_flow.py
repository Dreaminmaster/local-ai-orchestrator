import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.api import web_ai_profiles
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.workspace_manager import (
    ExternalAIWorkspaceManager,
    WorkspaceStatus,
)


class SlowBrowser:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.contexts = {}
        self.last_launch_details = {}
        self.new_page_calls = 0
        self.release = asyncio.Event()

    async def new_page(self, provider, headless=False):
        self.new_page_calls += 1
        self.last_launch_details[provider] = {
            "browser_started": True,
            "page_created": True,
            "visible_window_expected": True,
        }
        await self.release.wait()
        page = FakePage()
        self.contexts[provider] = object()
        return page

    async def close_context(self, provider):
        self.contexts.pop(provider, None)

    async def close_all(self):
        self.contexts.clear()


class FakePage:
    url = "https://claude.ai/new"

    def is_closed(self):
        return False

    async def bring_to_front(self):
        return None

    def locator(self, selector):
        return FakeLocator(selector)


class FakeLocator:
    def __init__(self, selector):
        self.selector = selector
        self.last = self

    async def inner_text(self, timeout=0):
        return ""

    async def count(self):
        return 1

    async def is_visible(self, timeout=0):
        return True


class WorkspaceOpenProductFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_open_requests_create_one_browser_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ExternalAIWorkspaceManager(base_dir=str(Path(tmp) / "profiles"))
            manager.browser = SlowBrowser(Path(tmp) / "profiles")
            first = asyncio.create_task(manager.open_workspace("claude"))
            await asyncio.sleep(0)
            self.assertIn("claude", manager.opening_providers)
            status = await manager.get_workspace_status("claude")
            self.assertEqual(status.state, ProviderState.OPENING)
            second = asyncio.create_task(manager.open_workspace("claude"))
            manager.browser.release.set()
            page_one, page_two = await asyncio.gather(first, second)
            self.assertIs(page_one, page_two)
            self.assertEqual(manager.browser.new_page_calls, 1)

    async def test_open_api_returns_clear_browser_missing_error(self):
        status = WorkspaceStatus(
            provider="claude",
            state=ProviderState.NOT_CONFIGURED,
            profile_dir="/tmp/app-data/runtime/browser_profiles/claude",
        )
        fake_manager = AsyncMock()
        fake_manager.open_request_ids = {}
        fake_manager.get_workspace_status.return_value = status
        with patch.object(web_ai_profiles, "workspace_manager", fake_manager), patch.object(
            web_ai_profiles,
            "playwright_status_payload",
            return_value={
                "configured_path": "/tmp/app-data/playwright-browsers",
                "exists": True,
                "chromium_found": False,
            },
        ), patch.object(
            web_ai_profiles, "_profile_dir", return_value=Path("/tmp/app-data/runtime/browser_profiles")
        ):
            result = await web_ai_profiles.open_workspace(
                "claude", {"request_id": "one-click-request"}
            )
        self.assertEqual(result["request_id"], "one-click-request")
        self.assertEqual(result["failure_code"], "PROJECT_BROWSER_MISSING")
        self.assertFalse(result["browser_started"])
        fake_manager.open_workspace.assert_not_called()

    def test_frontend_has_single_request_guard_and_loading_state(self):
        source = (Path(__file__).resolve().parents[1] / "frontend/app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("const workspaceOpenRequests = new Map()", source)
        self.assertIn("if (workspaceOpenRequests.has(provider))", source)
        self.assertIn("button.disabled = loading", source)
        self.assertIn('button.textContent = loading ? "正在打开…"', source)
        self.assertEqual(
            source.count("log(`打开 ${provider} 项目专用工作区… request=${requestId}`"),
            1,
        )

    def test_default_workspace_profile_path_uses_runtime_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            with patch.dict(
                os.environ,
                {
                    "PROJECT_ROOT": tmp,
                    "LOCAL_AI_RUNTIME_DIR": str(runtime),
                    "PLAYWRIGHT_BROWSERS_PATH": str(Path(tmp) / "playwright-browsers"),
                },
                clear=False,
            ):
                manager = ExternalAIWorkspaceManager()
            self.assertEqual(
                manager.browser.base_dir.resolve(), (runtime / "browser_profiles").resolve()
            )
            self.assertTrue(manager.browser.base_dir.is_absolute())

    def test_backend_startup_rebinds_early_workspace_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            manager = ExternalAIWorkspaceManager(base_dir="runtime/browser_profiles")
            with patch.dict(
                os.environ,
                {
                    "PROJECT_ROOT": tmp,
                    "LOCAL_AI_RUNTIME_DIR": str(runtime),
                    "PLAYWRIGHT_BROWSERS_PATH": str(Path(tmp) / "playwright-browsers"),
                },
                clear=False,
            ):
                configured = manager.configure_runtime_paths()
            self.assertEqual(configured, (runtime / "browser_profiles").resolve())
            self.assertEqual(manager.browser.base_dir, configured)


if __name__ == "__main__":
    unittest.main()
