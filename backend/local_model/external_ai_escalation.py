from __future__ import annotations

import json
from pathlib import Path


class ExternalAIEscalationRouter:
    REPORT_DIR = Path("runtime/test_reports/web_ai")
    STATUS_RANK = {
        "PASS": 0,
        "PARTIAL": 1,
        "FAIL": 2,
        "NOT_RUN": 3,
    }
    PROVIDER_LABELS = {
        "claude": "Claude Web",
        "chatgpt": "ChatGPT Web",
    }
    REASON_PROVIDER_WEIGHT = {
        "code_repair_failed": {"claude": 0, "chatgpt": 1},
        "external_ai_needed": {"claude": 0, "chatgpt": 1},
        "planner_uncertain": {"claude": 0, "chatgpt": 1},
    }

    def should_escalate(self, reason: str, state: dict) -> bool:
        if state.get("json_parse_failures", 0) >= 2:
            return True
        if state.get("retry_count", 0) >= 2:
            return True
        return reason in [
            "visual_judgment_required",
            "code_repair_failed",
            "external_ai_needed",
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
        web_target = self._choose_web_target(reason, available_external_ai)
        if web_target:
            return web_target
        preferred = {
            "visual_judgment_required": [
                "Claude Web",
                "ChatGPT Web",
                "ChatGPT",
                "Gemini",
                "Claude",
            ],
            "code_repair_failed": [
                "Claude Web",
                "Codex",
                "ChatGPT Web",
                "Claude",
                "ChatGPT",
            ],
            "external_ai_needed": ["Claude Web", "ChatGPT Web", "Claude", "ChatGPT"],
            "fresh_information_required": ["Perplexity", "ChatGPT", "Gemini"],
        }.get(reason, available_external_ai)
        for t in preferred:
            if self._target_available(t, available_external_ai):
                return self._canonical_target(t)
        return available_external_ai[0] if available_external_ai else None

    def _choose_web_target(
        self, reason: str, available_external_ai: list[str]
    ) -> str | None:
        candidates = []
        provider_weight = self.REASON_PROVIDER_WEIGHT.get(reason, {})
        for provider, label in self.PROVIDER_LABELS.items():
            if not self._provider_available(provider, available_external_ai):
                continue
            status = self._provider_status(provider)
            candidates.append(
                (
                    self.STATUS_RANK.get(status, self.STATUS_RANK["NOT_RUN"]),
                    provider_weight.get(provider, 10),
                    label,
                    status,
                )
            )
        if not candidates:
            return None
        best_status_rank, _, best_label, _ = sorted(candidates)[0]
        if best_status_rank <= self.STATUS_RANK["PARTIAL"]:
            return best_label
        return None

    def _provider_status(self, provider: str) -> str:
        report = self.REPORT_DIR / f"{provider}.json"
        if not report.exists():
            return "NOT_RUN"
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except Exception:
            return "FAIL"
        if (
            data.get("success")
            and data.get("answer_quality", {}).get("quality") == "PASS"
        ):
            return "PASS"
        if data.get("login_detection") and (
            data.get("send_prompt")
            or data.get("extract_answer")
            or data.get("evidence_saved")
        ):
            return "PARTIAL"
        return "FAIL"

    def _provider_available(
        self, provider: str, available_external_ai: list[str]
    ) -> bool:
        return any(
            self._provider_key(target) == provider for target in available_external_ai
        )

    def _target_available(self, target: str, available_external_ai: list[str]) -> bool:
        target_key = self._provider_key(target)
        normalized_target = self._normalize_target(target)
        return any(
            self._provider_key(item) == target_key
            or self._normalize_target(item) == normalized_target
            for item in available_external_ai
        )

    def _provider_key(self, target: str) -> str:
        normalized = self._normalize_target(target)
        if normalized.startswith("claude"):
            return "claude"
        if normalized.startswith("chatgpt"):
            return "chatgpt"
        return normalized

    def _canonical_target(self, target: str) -> str:
        provider = self._provider_key(target)
        return self.PROVIDER_LABELS.get(provider, target)

    def _normalize_target(self, target: str) -> str:
        return target.lower().replace(" ", "").replace("_", "").replace("-", "")
