import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import beta_validation


class BetaValidationStatusTests(unittest.TestCase):
    def test_need_user_intervention_is_not_blocking_failure(self):
        checks = [
            {"name": "health_check", "status": "PASS", "returncode": 0, "cmd": "health", "stdout_tail": "", "stderr_tail": ""},
            {"name": "repair_matrix", "status": "PASS", "returncode": 0, "cmd": "repair", "stdout_tail": "", "stderr_tail": ""},
            {
                "name": "live_claude_workspace_e2e",
                "status": "NEED_USER_INTERVENTION",
                "returncode": 0,
                "cmd": "live",
                "stdout_tail": "",
                "stderr_tail": "",
            },
        ]

        with patch.object(beta_validation, "REPORT", Path("/tmp/beta_validation_test.md")):
            beta_validation.write_report(checks, live_requested=True)
            text = Path("/tmp/beta_validation_test.md").read_text(encoding="utf-8")

        self.assertIn("Overall: **PASS**", text)
        self.assertIn("workspace_needs_user: `true`", text)
        self.assertIn("blocking_failures: `0`", text)


if __name__ == "__main__":
    unittest.main()
