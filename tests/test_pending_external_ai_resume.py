import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api import external_ai_actions
from backend.skills.base import SkillResult
from backend.skills.external_ai_web.pending_action import PendingExternalAIStore
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.web_ai_skill import WebAISkill
from backend.skills.external_ai_web.workspace_manager import WorkspaceStatus


class FakeWorkspaceManager:
    def __init__(self, state):
        self.state = state
        self.last_recoveries = {}
        self.last_statuses = {
            "claude": WorkspaceStatus(
                provider="claude",
                state=state,
                profile_dir="runtime/browser_profiles/claude",
                page_url="https://claude.ai/new",
                need_user_intervention=state != ProviderState.READY,
            )
        }

    async def ensure_workspace(self, provider):
        return None

    async def get_workspace_status(self, provider):
        return self.last_statuses["claude"]


class FakeReadyWorkspaceManager(FakeWorkspaceManager):
    def __init__(self):
        super().__init__(ProviderState.READY)


class FakeSuccessWebAISkill:
    async def execute(self, instruction, context):
        return SkillResult(
            "web_ai",
            True,
            "answer",
            evidence=["runtime/evidence/web_ai/claude/fake"],
            metadata={"quality_check": {"quality": "PASS"}},
        )


class PendingExternalAIResumeTests(unittest.IsolatedAsyncioTestCase):
    async def test_web_ai_need_user_intervention_saves_pending_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PendingExternalAIStore(Path(tmp))
            with patch(
                "backend.skills.external_ai_web.web_ai_skill.pending_external_ai_store",
                store,
            ), patch(
                "backend.skills.external_ai_web.web_ai_skill.workspace_manager",
                FakeWorkspaceManager(ProviderState.NEED_LOGIN),
            ):
                result = await WebAISkill().execute(
                    "ask claude",
                    {
                        "task_id": "task_pending",
                        "step_index": 1,
                        "provider": "Claude Web",
                        "target": "Claude Web",
                        "prompt": "original prompt",
                        "reuse_workspace": True,
                    },
                )

            pending = store.load("task_pending")
            self.assertFalse(result.success)
            self.assertTrue(result.metadata["need_user_intervention"])
            self.assertEqual(pending["task_id"], "task_pending")
            self.assertEqual(pending["step_id"], "step_2")
            self.assertEqual(pending["provider"], "claude")
            self.assertTrue(pending["can_resume"])

    async def test_resume_still_need_login_does_not_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PendingExternalAIStore(Path(tmp))
            store.save(
                task_id="task_login",
                step_id="step_1",
                provider="claude",
                original_prompt="original",
                redacted_prompt="redacted",
                context={"task_id": "task_login"},
                provider_status="NEED_LOGIN",
                failure_reason="claude_profile_missing_or_not_logged_in",
                suggested_user_action="log in",
            )
            with patch.object(external_ai_actions, "pending_external_ai_store", store), patch.object(
                external_ai_actions,
                "workspace_manager",
                FakeWorkspaceManager(ProviderState.NEED_LOGIN),
            ), patch.object(external_ai_actions, "WebAISkill", side_effect=AssertionError("should not send")):
                result = await external_ai_actions.resume_pending_external_ai("task_login")

            self.assertTrue(result["still_needs_user"])
            self.assertEqual(result["provider_status"], ProviderState.NEED_LOGIN.value)

    async def test_resume_ready_executes_pending_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PendingExternalAIStore(Path(tmp))
            store.save(
                task_id="task_ready",
                step_id="step_1",
                provider="claude",
                original_prompt="original",
                redacted_prompt="redacted",
                context={"task_id": "task_ready"},
                provider_status="NEED_LOGIN",
                failure_reason="claude_profile_missing_or_not_logged_in",
                suggested_user_action="log in",
            )
            with patch.object(external_ai_actions, "pending_external_ai_store", store), patch.object(
                external_ai_actions,
                "workspace_manager",
                FakeReadyWorkspaceManager(),
            ), patch.object(external_ai_actions, "WebAISkill", return_value=FakeSuccessWebAISkill()):
                result = await external_ai_actions.resume_pending_external_ai("task_ready")

            self.assertFalse(result["still_needs_user"])
            self.assertTrue(result["success"])
            self.assertFalse(store.load("task_ready"))


if __name__ == "__main__":
    unittest.main()
