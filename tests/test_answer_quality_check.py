import unittest

from backend.skills.external_ai_web.answer_quality_check import AnswerQualityChecker


class AnswerQualityCheckTests(unittest.TestCase):
    def test_network_terms_in_normal_answer_do_not_trigger_network_error(self):
        answer = (
            "Use a clear network architecture diagram, document the connection "
            "between modules, and define a timeout strategy for slow tasks."
        )

        quality = AnswerQualityChecker().check(answer)

        self.assertEqual(quality["quality"], "PASS")
        self.assertNotIn("network_error", quality["issues"])

    def test_explicit_network_error_phrases_trigger_network_error(self):
        examples = [
            "Network error: unable to connect to Claude.",
            "Connection lost. Reconnecting...",
            "The request timed out.",
            "网络错误：无法连接到 Claude 服务，请稍后再试。",
            "请求超时，请稍后再试，当前页面暂时无法完成响应。",
        ]

        for answer in examples:
            with self.subTest(answer=answer):
                quality = AnswerQualityChecker().check(answer)
                self.assertEqual(quality["quality"], "PARTIAL")
                self.assertIn("network_error", quality["issues"])


if __name__ == "__main__":
    unittest.main()
