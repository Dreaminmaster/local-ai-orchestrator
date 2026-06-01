from __future__ import annotations

import json
from pathlib import Path


class ExternalAIEscalationRouter:
    REPORT_DIR = Path("runtime/test_reports/web_ai")

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
        ]

    def choose_target(
        self, reason: str, available_external_ai: list[str]
    ) -> str | None:
        web_target = self._choose_web_target(available_external_ai)
        if web_target:
            return web_target
        preferred = {
            "visual_judgment_required": ["ChatGPT", "Gemini", "Claude"],
            "code_repair_failed": ["Codex", "Claude", "ChatGPT"],
            "fresh_information_required": ["Perplexity", "ChatGPT", "Gemini"],
        }.get(reason, available_external_ai)
        for t in preferred:
            if t in available_external_ai:
                return t
        return available_external_ai[0] if available_external_ai else None

    def _choose_web_target(self, available_external_ai: list[str]) -> str | None:
        available = {a.lower().replace(" ", "") for a in available_external_ai}
        candidates = []
        for provider, label in [("claude", "Claude Web"), ("chatgpt", "ChatGPT Web")]:
            if provider not in available and f"{provider}web" not in available:
                continue
            status = self._provider_status(provider)
            if status == "PASS":
                candidates.append((0, label))
            elif status == "PARTIAL":
                candidates.append((1, label))
        return sorted(candidates)[0][1] if candidates else None

    def _provider_status(self, provider: str) -> str:
        report = self.REPORT_DIR / f"{provider}.json"
        if not report.exists():
            return "NOT_RUN"
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except Exception:
            return "FAIL"
        if data.get("success") and data.get("answer_quality", {}).get("quality") == "PASS":
            return "PASS"
        if data.get("login_detection") and (
            data.get("send_prompt") or data.get("extract_answer") or data.get("evidence_saved")
        ):
            return "PARTIAL"
        return "FAIL"
