import unittest

from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.workspace_manager import ExternalAIWorkspaceManager


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
    def __init__(self, text="", url="https://claude.ai/new", input_visible=False):
        self.text = text
        self.url = url
        self.input_visible = input_visible
        self.goto_calls = []
        self.closed = False

    def is_closed(self):
        return self.closed

    def locator(self, selector):
        return FakeLocator(self, selector)

    async def goto(self, url, wait_until="domcontentloaded", timeout=0):
        self.goto_calls.append(url)
        self.url = url
        self.text = ""
        self.input_visible = True


class FailingRecoveryPage(FakePage):
    async def goto(self, url, wait_until="domcontentloaded", timeout=0):
        self.goto_calls.append(url)
        self.url = url
        self.text = "Conversation not found"
        self.input_visible = False


class WorkspaceRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_claude_conversation_not_found_is_stale(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(text="This conversation could not be found. Conversation not found.")
        state = await manager.detect_page_state(page, "Claude Web")
        self.assertEqual(state, ProviderState.STALE_CONVERSATION)

    async def test_claude_login_prompt_is_need_login(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(text="Sign in Continue with Google", url="https://claude.ai/login")
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.NEED_LOGIN)

    async def test_claude_visible_input_is_ready(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(text="Good afternoon", input_visible=True)
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.READY)

    async def test_normal_answer_containing_not_found_is_not_stale(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(
            text="If the variable is not found, define it before use.",
            url="https://claude.ai/chat/current",
            input_visible=True,
        )
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.READY)

    async def test_stale_phrase_with_visible_composer_is_ready(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(
            text="Earlier message: Conversation not found",
            url="https://claude.ai/chat/current",
            input_visible=True,
        )
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.READY)

    async def test_stale_conversation_triggers_recover_workspace(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(text="Conversation not found", url="https://claude.ai/chat/stale")
        manager.pages["claude"] = page
        recovery = await manager.recover_workspace("Claude Web", "stale_conversation")
        self.assertTrue(recovery["recovered"])
        self.assertEqual(recovery["action_taken"], "navigate_to_new_conversation")
        self.assertEqual(recovery["before_url"], "https://claude.ai/chat/stale")
        self.assertEqual(recovery["after_url"], "https://claude.ai/new")
        self.assertEqual(recovery["status_after_recovery"], ProviderState.READY.value)

    async def test_recovery_failure_requires_intervention_and_no_fallback(self):
        manager = ExternalAIWorkspaceManager()
        page = FailingRecoveryPage(
            text="Conversation not found", url="https://claude.ai/chat/stale"
        )
        manager.pages["claude"] = page
        recovery = await manager.recover_workspace("Claude Web", "stale_conversation")
        self.assertFalse(recovery["recovered"])
        self.assertEqual(
            recovery["status_after_recovery"],
            ProviderState.NEED_USER_INTERVENTION.value,
        )
        self.assertNotIn("chatgpt", manager.pages)

    async def test_page_network_error_requires_intervention_state(self):
        manager = ExternalAIWorkspaceManager()
        page = FakePage(text="Network error. Unable to connect. Reconnecting...")
        state = await manager.detect_page_state(page, "claude")
        self.assertEqual(state, ProviderState.PAGE_NETWORK_ERROR)


if __name__ == "__main__":
    unittest.main()
