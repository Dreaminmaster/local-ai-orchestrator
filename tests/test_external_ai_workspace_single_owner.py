import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.workspace_manager import (
    ExternalAIWorkspaceManager,
    ProfileInUseByBackend,
)


class FakePage:
    def __init__(self, *, text="", input_visible=True):
        self.url = "https://claude.ai/new"
        self.text = text
        self.input_visible = input_visible
        self.closed = False
        self.bring_to_front_calls = 0

    def is_closed(self):
        return self.closed

    def locator(self, selector):
        return FakeLocator(self, selector)

    async def goto(self, url, **kwargs):
        self.url = url

    async def bring_to_front(self):
        self.bring_to_front_calls += 1


class FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.last = self

    async def inner_text(self, timeout=0):
        return self.page.text

    async def count(self):
        return 1 if self.selector == "body" or self.page.input_visible else 0

    async def is_visible(self, timeout=0):
        return self.page.input_visible


class FakeBrowser:
    def __init__(self, base_dir, page=None):
        self.base_dir = Path(base_dir)
        self.page = page or FakePage()
        self.contexts = {}
        self.new_page_calls = 0
        self.closed = []

    async def new_page(self, provider, headless=False):
        self.new_page_calls += 1
        self.contexts[provider] = object()
        return self.page

    async def close_context(self, provider):
        self.closed.append(provider)
        self.contexts.pop(provider, None)

    async def close_all(self):
        self.contexts.clear()


class ExternalAIWorkspaceSingleOwnerTests(unittest.IsolatedAsyncioTestCase):
    def make_manager(self, tmp):
        base_dir = Path(tmp) / "profiles"
        manager = ExternalAIWorkspaceManager(base_dir=str(base_dir))
        manager.browser = FakeBrowser(base_dir)
        return manager

    async def test_ready_workspace_reuses_existing_page_without_second_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            first = await manager.open_workspace("claude")
            second = await manager.ensure_workspace("claude")
            self.assertIs(first, second)
            self.assertEqual(manager.browser.new_page_calls, 1)
            self.assertTrue(manager.workspace_reused["claude"])
            status = await manager.get_workspace_status("claude")
            self.assertTrue(status.workspace_reused)
            self.assertTrue(status.workspace_already_open)
            self.assertTrue(status.same_window_focused)
            self.assertFalse(status.new_context_created)
            self.assertFalse(status.second_context_created)
            self.assertTrue(status.workspace_id.startswith("claude-"))

    async def test_second_open_focuses_existing_workspace_and_keeps_workspace_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            first = await manager.open_workspace("claude")
            first_status = await manager.get_workspace_status("claude")
            second = await manager.open_workspace("claude")
            second_status = await manager.get_workspace_status("claude")
            self.assertIs(first, second)
            self.assertEqual(manager.browser.new_page_calls, 1)
            self.assertEqual(first_status.workspace_id, second_status.workspace_id)
            self.assertTrue(second_status.workspace_reused)
            self.assertTrue(second_status.workspace_already_open)
            self.assertTrue(second_status.same_window_focused)
            self.assertFalse(second_status.new_context_created)
            self.assertFalse(second_status.second_context_created)
            self.assertGreaterEqual(first.bring_to_front_calls, 1)

    async def test_kimi_second_open_uses_same_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            first = await manager.open_workspace("kimi")
            second = await manager.open_workspace("kimi")
            status = await manager.get_workspace_status("kimi")
            self.assertIs(first, second)
            self.assertEqual(manager.browser.new_page_calls, 1)
            self.assertTrue(status.workspace_reused)
            self.assertTrue(status.workspace_already_open)
            self.assertTrue(status.same_window_focused)
            self.assertFalse(status.second_context_created)

    async def test_two_provider_requests_run_serially(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            order = []

            async def run(name):
                async with manager.provider_request("claude", name):
                    order.append(f"{name}:start")
                    await asyncio.sleep(0.02)
                    order.append(f"{name}:end")

            await asyncio.gather(run("one"), run("two"))
            self.assertEqual(order, ["one:start", "one:end", "two:start", "two:end"])

    async def test_busy_request_does_not_open_second_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            await manager.open_workspace("claude")
            async with manager.provider_request("claude", "request-1"):
                await manager.ensure_workspace("claude")
                status = await manager.get_workspace_status("claude")
                self.assertEqual(status.state, ProviderState.BUSY)
            self.assertEqual(manager.browser.new_page_calls, 1)

    async def test_active_other_backend_owner_is_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            owner_path = manager._owner_path("claude")
            owner_path.parent.mkdir(parents=True, exist_ok=True)
            owner_path.write_text(
                json.dumps(
                    {
                        "provider": "claude",
                        "owner_pid": manager.owner_pid,
                        "owner_type": "backend",
                        "app_instance_id": "another-backend",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ProfileInUseByBackend):
                await manager.open_workspace("claude")
            self.assertEqual(manager.browser.new_page_calls, 0)

    async def test_stale_owner_pid_is_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            owner_path = manager._owner_path("claude")
            owner_path.parent.mkdir(parents=True, exist_ok=True)
            owner_path.write_text(
                json.dumps(
                    {
                        "provider": "claude",
                        "owner_pid": 99999999,
                        "owner_type": "backend",
                        "app_instance_id": "stale",
                    }
                ),
                encoding="utf-8",
            )
            await manager.open_workspace("claude")
            owner = manager.inspect_owner("claude")
            self.assertEqual(owner["owner_pid"], manager.owner_pid)
            self.assertEqual(owner["app_instance_id"], manager.app_instance_id)

    async def test_closed_page_with_active_owner_is_crashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            page = await manager.open_workspace("claude")
            page.closed = True
            status = await manager.get_workspace_status("claude")
            self.assertEqual(status.state, ProviderState.CRASHED)

    async def test_shutdown_releases_owner_and_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            await manager.open_workspace("claude")
            owner_path = manager._owner_path("claude")
            self.assertTrue(owner_path.exists())
            await manager.shutdown()
            self.assertFalse(owner_path.exists())
            self.assertIn("claude", manager.browser.closed)

    async def test_owner_file_contains_no_sensitive_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            await manager.open_workspace("claude")
            owner = json.loads(manager._owner_path("claude").read_text(encoding="utf-8"))
            self.assertEqual(
                set(owner),
                {
                    "provider",
                    "owner_pid",
                    "owner_type",
                    "started_at",
                    "profile_dir",
                    "app_instance_id",
                },
            )
            self.assertNotIn("cookie", json.dumps(owner).lower())

    async def test_need_login_is_detected_before_ready_composer(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.make_manager(tmp)
            page = FakePage(text="Continue with Google", input_visible=True)
            state = await manager.detect_page_state(page, "claude")
            self.assertEqual(state, ProviderState.NEED_LOGIN)

    def test_live_e2e_uses_backend_api_and_not_direct_workspace(self):
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "e2e_external_ai_live_workflow.py"
        ).read_text(encoding="utf-8")
        self.assertIn("/api/external-ai/workspaces/claude/ask", script)
        self.assertNotIn("launch_persistent_context", script)
        self.assertNotIn('"chatgpt"', script.lower())


if __name__ == "__main__":
    unittest.main()
