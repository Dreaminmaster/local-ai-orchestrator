from __future__ import annotations

from backend.settings_store import SettingsStore
from backend.skills.external_ai_web.provider_status import load_provider_report, state_from_report


class ExternalAIEscalationRouter:
    """Choose only enabled, tested web providers allowed by product settings."""

    STATUS_RANK = {"PASS": 0, "PARTIAL": 1, "DEGRADED": 2}
    PROVIDER_LABELS = {
        "claude": "Claude Web",
        "chatgpt": "ChatGPT Web",
        "gemini": "Gemini Web",
        "kimi": "Kimi Web",
        "doubao": "豆包 Web",
    }
    REASON_PROVIDER_WEIGHT = {
        "code_repair_failed": {"claude": 0, "chatgpt": 1, "gemini": 2, "kimi": 3, "doubao": 4},
        "external_ai_needed": {"claude": 0, "chatgpt": 1, "gemini": 2, "kimi": 3, "doubao": 4},
        "planner_uncertain": {"claude": 0, "chatgpt": 1, "gemini": 2, "kimi": 3, "doubao": 4},
    }

    def __init__(self, settings: SettingsStore | None = None):
        self.settings_store = settings or SettingsStore()

    def should_escalate(self, reason: str, state: dict) -> bool:
        if state.get("json_parse_failures", 0) >= 2 or state.get("retry_count", 0) >= 2:
            return True
        return reason in {
            "visual_judgment_required",
            "code_repair_failed",
            "external_ai_needed",
            "fresh_information_required",
            "planner_uncertain",
            "goal_unclear",
            "json_parse_failed",
            "local_model_uncertain",
            "context_overflow",
        }

    def choose_target(self, reason: str, available_external_ai: list[str]) -> str | None:
        settings = self.settings_store.load().get("external_ai", {})
        if settings.get("routing_policy") == "fully_local":
            return None
        if not settings.get("allow_automatic") and not settings.get("require_confirmation"):
            return None
        configured = settings.get("providers", {})
        available = {self._provider_key(item) for item in available_external_ai}
        priority = settings.get("priority") or list(self.PROVIDER_LABELS)
        weights = self.REASON_PROVIDER_WEIGHT.get(reason, {})
        candidates = []
        for index, provider in enumerate(priority):
            if provider not in available or not configured.get(provider, {}).get("enabled"):
                continue
            status = self._provider_status(provider)
            if status not in self.STATUS_RANK:
                continue
            candidates.append(
                (
                    self.STATUS_RANK[status],
                    weights.get(provider, index + 10),
                    index,
                    provider,
                )
            )
        if not candidates:
            return None
        return self.PROVIDER_LABELS[sorted(candidates)[0][-1]]

    def _provider_status(self, provider: str) -> str:
        report = load_provider_report(provider)
        if not report:
            return "NOT_CONFIGURED"
        state = state_from_report(provider, report).value
        return "DEGRADED" if state == "PARTIAL" else state

    def _provider_key(self, target: str) -> str:
        normalized = target.lower().replace(" ", "").replace("_", "").replace("-", "")
        if normalized.startswith("claude"):
            return "claude"
        if normalized.startswith("chatgpt"):
            return "chatgpt"
        if normalized.startswith("gemini"):
            return "gemini"
        if normalized.startswith("kimi"):
            return "kimi"
        if normalized.startswith("doubao") or normalized.startswith("豆包"):
            return "doubao"
        return normalized
