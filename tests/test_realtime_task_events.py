import tempfile
import unittest
from pathlib import Path

from backend.core.real_project_runner import RealProjectRunner
from backend.core.task_artifact_store import TaskArtifactStore


class RealtimeTaskEventTests(unittest.TestCase):
    def test_events_are_persisted_bounded_and_resume_from_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskArtifactStore(Path(tmp))
            first = store.append_event(
                "task-1",
                "tool_output",
                summary="safe",
                safe_payload={"stdout": "x" * 3000, "token": "must-not-appear"},
            )
            second = store.append_event("task-1", "task_completed", summary="done")

            self.assertEqual(first["event_id"], 1)
            self.assertEqual(second["event_id"], 2)
            self.assertNotIn("token", first["safe_payload"])
            self.assertLess(len(first["safe_payload"]["stdout"]), 1300)
            self.assertEqual(
                [event["event_id"] for event in store.list_events("task-1", after_event_id=1)],
                [2],
            )

    def test_real_project_emits_complete_realtime_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            tasks = Path(tmp) / "tasks"
            root.mkdir()
            (root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")

            result = RealProjectRunner(tasks).run(root, "verify project")
            events = TaskArtifactStore(tasks).list_events(result["task_id"])
            types = [event["event_type"] for event in events]

            self.assertEqual(result["final_status"], "PASS")
            for required in (
                "task_created",
                "goal_contract_created",
                "plan_created",
                "step_started",
                "tool_output",
                "verification_result",
                "final_report_ready",
                "task_completed",
            ):
                self.assertIn(required, types)
            self.assertEqual(len(types), len({event["event_id"] for event in events}))


if __name__ == "__main__":
    unittest.main()
