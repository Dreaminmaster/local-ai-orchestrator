class ExternalAIEscalationRouter:
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
        reasons = {
            "visual_judgment_required": ["ChatGPT", "Gemini", "Claude Web"],
            "code_repair_failed": ["Codex", "Claude Web", "ChatGPT"],
            "fresh_information_required": ["Perplexity", "ChatGPT", "Gemini"],
        }
        preferred = reasons.get(
            reason, ["Claude Web", "ChatGPT", "Gemini", "Kimi", "Codex"]
        )
        for t in preferred:
            if t in available_external_ai:
                return t
        return available_external_ai[0] if available_external_ai else None
