import tempfile
import unittest
from pathlib import Path

from backend.core.task_action_compiler import TaskActionCompiler
from backend.core.verifier import Verifier


class TaskActionCompilerTests(unittest.TestCase):
    def setUp(self):
        self.compiler = TaskActionCompiler()

    def auth(self, project_path):
        return {"provided_resources": {"project_path": str(project_path)}}

    def test_compile_file_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = self.compiler.compile(
                {
                    "original_input": (
                        "创建 hello.txt，内容写入 Local AI Orchestrator smoke test，"
                        "然后读取它并生成总结报告。"
                    )
                },
                self.auth(tmp),
            )
        self.assertEqual([step["needed_skills"][0] for step in steps], ["file", "file"])
        self.assertEqual(steps[0]["tool_context"]["action"], "write_file")
        self.assertEqual(
            steps[0]["tool_context"]["content"], "Local AI Orchestrator smoke test"
        )
        self.assertEqual(steps[1]["tool_context"]["action"], "read_file")

    def test_compile_shell_output_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = self.compiler.compile(
                {"original_input": "运行 python3 --version，并把结果写入 report.md。"},
                self.auth(tmp),
            )
        self.assertEqual([step["needed_skills"][0] for step in steps], ["shell", "file"])
        self.assertEqual(steps[0]["tool_context"]["command"], "python3 --version")
        self.assertTrue(steps[1]["tool_context"]["content_from_previous_stdout"])

    def test_compile_python_nameerror_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "main.py").write_text("print(message)\n", encoding="utf-8")
            steps = self.compiler.compile(
                {
                    "original_input": (
                        "运行这个项目，如果失败，请修复它，然后重新运行，最后写修复报告。"
                    ),
                    "final_goal": "修复 main.py",
                },
                self.auth(tmp),
            )
        self.assertEqual(
            [step["needed_skills"][0] for step in steps],
            ["shell", "file", "shell", "file"],
        )
        self.assertTrue(steps[0]["tool_context"]["continue_on_failure"])
        self.assertIn("message =", steps[1]["tool_context"]["patch"])

    def test_compile_python_importerror_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "main.py").write_text(
                "def main():\n    import nonexistent_module\n    print('ok')\n\nmain()\n",
                encoding="utf-8",
            )
            steps = self.compiler.compile(
                {"original_input": "运行并修复 main.py 的 ImportError，重新运行成功并写修复报告。"},
                self.auth(tmp),
            )
        self.assertEqual(len(steps), 4)
        self.assertIn("targeted_replace", steps[1]["tool_context"]["patch"])

    def test_compile_python_syntaxerror_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "main.py").write_text("def main()\n    print('ok')\n", encoding="utf-8")
            steps = self.compiler.compile(
                {"original_input": "运行并修复 main.py 的 SyntaxError，重新运行成功并写修复报告。"},
                self.auth(tmp),
            )
        self.assertEqual(len(steps), 4)
        self.assertIn("targeted_replace", steps[1]["tool_context"]["patch"])

    def test_compile_pending_external_ai_mock(self):
        steps = self.compiler.compile(
            {"original_input": "执行 pending_external_ai_mock，模拟外部 AI 需要用户处理。"},
            self.auth("/tmp"),
        )
        self.assertTrue(steps[0]["tool_context"]["pending_external_ai_mock"])

    def test_compile_small_project_review_to_chinese_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "main.py").write_text("print(message)\n", encoding="utf-8")
            steps = self.compiler.compile(
                {
                    "original_input": (
                        "检查这个小项目，运行测试，修复明显错误，最后写一份中文修复报告。"
                    )
                },
                self.auth(tmp),
            )
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[-1]["tool_context"]["path"], "final_report.md")
        self.assertIn("项目修复报告", steps[-1]["tool_context"]["content"])


class GenericVerifierFallbackTests(unittest.TestCase):
    def test_generic_criteria_pass_with_successful_results_and_evidence(self):
        verifier = Verifier(llm=None)
        criteria = ["完成用户目标", "有证据证明结果", "输出最终报告"]
        mapped = [
            {"criterion": "完成用户目标", "evidence": []},
            {"criterion": "有证据证明结果", "evidence": [{"id": "ev1"}]},
            {"criterion": "输出最终报告", "evidence": []},
        ]
        result = verifier._heuristic_verify(
            criteria,
            mapped,
            [{"skill": "file", "success": True}],
        )
        self.assertTrue(result["verified"])
        self.assertFalse(result["missing_items"])


if __name__ == "__main__":
    unittest.main()
