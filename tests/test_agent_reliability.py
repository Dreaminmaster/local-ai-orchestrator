import tempfile
import unittest
from pathlib import Path

from backend.core.task_artifact_store import TaskArtifactStore
from backend.local_model.retry_policy import LocalModelRetryPolicy


class FakeResponse:
    status_code = 502


class FakeHttpError(Exception):
    response = FakeResponse()


class LocalModelRetryPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_502_returns_fallback_status_without_sensitive_attempts(self):
        class FailingLLM:
            async def chat(self, *args, **kwargs):
                raise FakeHttpError("secret response body")

        result = await LocalModelRetryPolicy(max_retries=1).run_with_retry(
            llm=FailingLLM(),
            build_prompt=lambda context, schema, attempt=0: "prompt",
            parser=type("Parser", (), {"parse": lambda self, value: None})(),
            context={},
            output_schema={},
            fallback={"plan": []},
        )
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["local_model_status"], "LOCAL_MODEL_ERROR")
        self.assertEqual(result["local_model_error_summary"], "FakeHttpError: HTTP 502")
        self.assertNotIn("secret", str(result))


class TaskArtifactStoreTests(unittest.TestCase):
    def test_task_directory_contains_state_plan_logs_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskArtifactStore(tmp)
            store.initialize("task-1", {"final_goal": "goal"}, {})
            store.save_plan("task-1", {"plan": [{"step": 1}], "total_steps": 1})
            store.append_step_log("task-1", {"type": "step_result", "success": True})
            report_path = store.save_report("task-1", "# Report")
            store.update_state("task-1", status="success", report_path=str(report_path))

            task_dir = Path(tmp, "task-1")
            self.assertTrue(Path(task_dir, "task_state.json").exists())
            self.assertTrue(Path(task_dir, "plan.json").exists())
            self.assertTrue(Path(task_dir, "step_logs.jsonl").exists())
            self.assertTrue(Path(task_dir, "final_report.md").exists())
            self.assertEqual(store.get("task-1")["status"], "success")
            self.assertEqual(store.get_report("task-1"), "# Report")


if __name__ == "__main__":
    unittest.main()
