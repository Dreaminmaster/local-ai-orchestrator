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

    def test_complete_answer_with_unavailable_banner_passes_with_warning(self):
        quality = AnswerQualityChecker().check(
            "Define the missing variable before using it, or correct the variable name.",
            warning_text="Claude Fable 5 is currently unavailable.",
            warning_class="non_blocking_warning",
        )
        self.assertEqual(quality["quality"], "PASS_WITH_WARNING")
        self.assertTrue(quality["reliable"])

    def test_no_answer_with_unavailable_banner_fails(self):
        quality = AnswerQualityChecker().check(
            "",
            warning_text="Claude Fable 5 is currently unavailable.",
            warning_class="blocking_error",
        )
        self.assertEqual(quality["quality"], "FAIL")

    def test_partial_answer_with_blocking_error_is_partial(self):
        quality = AnswerQualityChecker().check(
            "A partial answer was generated, but something went wrong.",
            warning_text="Something went wrong.",
            warning_class="blocking_error",
        )
        self.assertEqual(quality["quality"], "PARTIAL")

    def test_body_or_sidebar_source_never_passes(self):
        for answer in [
            "A plausible answer mixed with body fallback and error text.",
            "A plausible answer mixed with sidebar navigation and error text.",
        ]:
            with self.subTest(answer=answer):
                quality = AnswerQualityChecker().check(
                    answer,
                    reliable_answer=False,
                    warning_text="Claude Fable 5 is currently unavailable.",
                    warning_class="blocking_error",
                )
                self.assertEqual(quality["quality"], "FAIL")
                self.assertFalse(quality["reliable"])


if __name__ == "__main__":
    unittest.main()
