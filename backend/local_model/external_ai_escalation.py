import json
from pathlib import Path


class ExternalAIEscalationRouter:
    TEST_REPORT_DIR = Path("runtime/test_reports/web_ai")
    DEFAULT_PRIORITY = ["Claude Web", "ChatGPT", "Gemini", "Kimi", "Codex"]

    def should_escalate(self, reason: str, state: dict) -> bool:
        if state.get("json_parse_failures", 0) >= 2:
            return True
        if state.get("retry_count", 0) >= 2:
            return True
        return reason in [
            "visual_judgment_required",
            "code_repair_failed",
            "fresh_information_required",
            "planner_uncertain",
            "goal_unclear",
            "json_parse_failed",
            "local_model_uncertain",
            "context_overflow",
            "external_ai_needed",
        ]

    def choose_target(
        self, reason: str, available_external_ai: list[str]
    ) -> str | None:
        ranked = self._rank_by_test_results(
            reason, available_external_ai or self.DEFAULT_PRIORITY
        )
        return ranked[0] if ranked else None

    def _rank_by_test_results(self, reason: str, candidates: list[str]) -> list[str]:
        """Sort candidates by real test report status: PASS > PARTIAL > FAIL > untested."""
        provider_scores = {}
        for candidate in candidates:
            key = candidate.lower().replace(" ", "_").replace("-", "_")
            report_path = self.TEST_REPORT_DIR / f"{key}.json"
            score = 0
            if report_path.exists():
                try:
                    data = json.loads(report_path.read_text(encoding="utf-8"))
                    status = data.get("status", "")
                    aq = data.get("answer_quality", {})
                    if status == "success":
                        score = 3 if aq.get("quality") == "PASS" else 2
                    elif status == "partial" or data.get("login_detection"):
                        score = 1
                except Exception:
                    pass
            # Boost Claude for code repair
            if reason == "code_repair_failed" and "claude" in key:
                score += 1
            provider_scores[candidate] = score

        return sorted(candidates, key=lambda c: provider_scores.get(c, 0), reverse=True)
