import tempfile
import unittest
from pathlib import Path

from backend.core.real_project_runner import RealProjectRunner


class RealProjectRunnerTests(unittest.TestCase):
    def test_goal_contract_plan_resume_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            tasks = Path(tmp) / "tasks"
            root.mkdir()
            (root / "tests").mkdir()
            (root / "main.py").write_text(
                "def build_message(): return 'fixed'\n\ndef build():\n    UNDEFINED_MESSAGE\n    return message\n",
                encoding="utf-8",
            )
            (root / "tests/test_main.py").write_text(
                "import unittest\nfrom main import build\n"
                "class T(unittest.TestCase):\n"
                "    def test_build(self): self.assertEqual(build(), 'fixed')\n",
                encoding="utf-8",
            )
            runner = RealProjectRunner(tasks)
            interrupted = runner.run(root, "repair project", interrupt_after_step=2)
            self.assertEqual(interrupted["final_status"], "INTERRUPTED")

            result = runner.resume(interrupted["task_id"])

            self.assertEqual(result["final_status"], "PASS")
            state = runner.artifacts.read_json(result["task_id"], "task_state.json")
            self.assertTrue(state["resumed_from_checkpoint"])
            self.assertEqual(len(state["completed_steps"]), len(set(state["completed_steps"])))
            self.assertTrue(runner.list_checkpoints(result["task_id"]))
            rollback = runner.rollback(result["task_id"])
            self.assertTrue(rollback["success"])

    def test_checkpoint_and_rollback_preserve_project_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            tasks = Path(tmp) / "tasks"
            root.mkdir()
            (root / "tests").mkdir()
            (root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "tests/test_main.py").write_text(
                "import unittest\nfrom main import VALUE\n"
                "class T(unittest.TestCase):\n"
                "    def test_value(self): self.assertEqual(VALUE, 1)\n",
                encoding="utf-8",
            )
            (root / "target.py").write_text("print('target')\n", encoding="utf-8")
            (root / "link.py").symlink_to("target.py")
            runner = RealProjectRunner(tasks)
            result = runner.run(root, "verify symlink project")
            checkpoint = runner.list_checkpoints(result["task_id"])[0]
            self.assertTrue((Path(checkpoint["snapshot_path"]) / "link.py").is_symlink())

            (root / "link.py").unlink()
            rollback = runner.rollback(result["task_id"], checkpoint["checkpoint_id"])

            self.assertTrue(rollback["success"])
            self.assertTrue((root / "link.py").is_symlink())


if __name__ == "__main__":
    unittest.main()
