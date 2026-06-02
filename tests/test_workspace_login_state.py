import unittest
from unittest.mock import patch

from backend.skills.external_ai_web.claude_web_adapter import ClaudeWebAdapter
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.web_ai_skill import WebAISkill
from backend.skills.external_ai_web.workspace_manager import (
    ExternalAIWorkspaceManager,
    WorkspaceStatus,
)


class FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.last = self

    async def inner_text(self, timeout=0):
        return self.page.text

    async def count(self):
        if self.selector == "body":
            return 1
        return 1 if self.page.input_visible else 0

    async def is_visible(self, timeout=0):
        return self.page.input_visible

    async def wait_for(self, state="visible", timeout=0):
        if not self.page.input_visible:
            raise TimeoutError("input not visible")


class FakePage:
    url = "https://claude.ai/new"

    def __init__(self, text="", input_visible=False):
        self.text = text
        self.input_visible = input_visible

    def is_closed(self):
        return False

    def locator(self, selector):
        return FakeLocator(self, selector)

    async def screenshot(self, path, full_page=True):
        return None


class NoSendClaudeAdapter(ClaudeWebAdapter):
    def __init__(self, page):
        super().__init__(page=page)
        self.send_called = False

    async def open(self):
        return None

    async def send_prompt(self, prompt, attachments=None):
        self.send_called = True
        raise AssertionError("send_prompt should not be called when NEED_LOGIN")


class FakeWorkspaceManager:
    def __init__(self):
        self.last_recoveries = {}
        self.last_statuses = {
            "claude": WorkspaceStatus(
                provider="claude",
                state=ProviderState.NEED_LOGIN,
                profile_dir="runtime/browser_profiles/claude",
                page_url="https://claude.ai/new",
                need_user_intervention=True,
            )
        }

    async def ensure_workspace(self, provider):
        return FakePage(text="Continue with Google", input_visible=True)


class WorkspaceLoginStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_sign_in_prompt_is_need_login(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage("Sign in Log in Continue with Google")
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.NEED_LOGIN)

    async def test_session_expired_is_need_login(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage("Session expired. Please log in again.")
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.NEED_LOGIN)

    async def test_composer_with_login_modal_is_need_login_not_ready(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage("Continue with Google", input_visible=True)
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.NEED_LOGIN)

    async def test_claude_adapter_need_login_does_not_send_prompt(self):
        page = FakePage("Continue with Google", input_visible=True)
        adapter = NoSendClaudeAdapter(page)

        response = await adapter.ask("hello")

        self.assertTrue(response.needs_login)
        self.assertFalse(adapter.send_called)
        self.assertFalse(response.success)

    async def test_web_ai_skill_need_login_returns_user_intervention(self):
        with patch(
            "backend.skills.external_ai_web.web_ai_skill.workspace_manager",
            FakeWorkspaceManager(),
        ):
            result = await WebAISkill().execute(
                "ask claude",
                {"provider": "Claude Web", "target": "Claude Web", "reuse_workspace": True},
            )

        self.assertFalse(result.success)
        self.assertTrue(result.metadata["need_user_intervention"])
        self.assertTrue(result.metadata["can_resume"])
        self.assertEqual(result.metadata["provider_status"], ProviderState.NEED_LOGIN.value)
        self.assertIn("Recheck/Resume", result.metadata["suggested_user_action"])
        self.assertEqual(
            result.metadata["workspace_status"]["state"],
            ProviderState.NEED_LOGIN.value,
        )

    async def test_login_required_does_not_enter_answer_quality_issues(self):
        class Response:
            needs_login = True
            answer = ""

        quality = WebAISkill()._check_answer_quality(Response())

        self.assertEqual(quality["quality"], "BLOCKED")
        self.assertEqual(quality["reason"], "")


if __name__ == "__main__":
    unittest.main()
