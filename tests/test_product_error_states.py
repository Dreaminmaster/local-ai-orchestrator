import tempfile
import unittest
from pathlib import Path

from backend.core.product_errors import product_error
from backend.core.task_artifact_store import TaskArtifactStore
from backend.skills.external_ai_web.provider_status import ProviderState, profile_state


class ProductErrorStateTests(unittest.TestCase):
    def test_product_error_has_human_message_and_next_action(self):
        item = product_error("EXTERNAL_AI_NEED_LOGIN", detail="claude_login_required")
        self.assertIn("外部 AI", item["message"])
        self.assertIn("Claude", item["next_action"])
        self.assertEqual(item["detail"], "claude_login_required")

    def test_profile_directory_alone_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "claude"
            profile.mkdir()
            (profile / "Preferences").write_text("{}", encoding="utf-8")
            from backend.skills.external_ai_web import provider_status

            original = provider_status.profile_dir
            provider_status.profile_dir = lambda provider: root / provider
            try:
                self.assertEqual(profile_state("claude"), ProviderState.NEED_LOGIN)
            finally:
                provider_status.profile_dir = original

    def test_task_history_includes_tool_count_and_task_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskArtifactStore(tmp)
            store.initialize("task1", {"final_goal": "demo"}, {})
            store.append_step_log("task1", {"type": "step_result", "success": True})
            task = store.get("task1")
            self.assertEqual(task["tool_call_count"], 1)
            self.assertTrue(task["task_dir"].endswith("task1"))


if __name__ == "__main__":
    unittest.main()
