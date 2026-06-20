from backend.llm.base import LLMMessage


class LocalModelRetryPolicy:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def run_with_retry(
        self,
        llm,
        build_prompt,
        parser,
        context,
        output_schema,
        fallback,
        escalation_router=None,
    ):
        attempts = []
        error_summaries = []
        for attempt in range(self.max_retries):
            prompt = build_prompt(context, output_schema, attempt=attempt)
            try:
                raw = await llm.chat(
                    [LLMMessage(role="user", content=prompt)],
                    temperature=0.2,
                    json_mode=True,
                )
                parsed = parser.parse(
                    raw.content if hasattr(raw, "content") else str(raw)
                )
                if parsed:
                    return parsed
                attempts.append(raw)
            except Exception as exc:
                attempts.append(exc)
                error_summaries.append(self._safe_error_summary(exc))
            context = self._shrink_context(context)
        fallback = dict(fallback)
        fallback.update(
            {
                "local_model_status": self._status_from_errors(error_summaries),
                "fallback_used": True,
                "local_model_error_summary": error_summaries[-1]
                if error_summaries
                else "Local model returned invalid JSON",
            }
        )
        if escalation_router and escalation_router.should_escalate(
            "json_parse_failed", {"json_parse_failures": len(attempts)}
        ):
            fallback.update(
                {
                    "needs_escalation": True,
                    "reason": "Local model failed to produce valid JSON or was unreachable",
                    "attempt_count": len(attempts),
                }
            )
            return fallback
        return fallback

    def _safe_error_summary(self, exc: Exception) -> str:
        """Return a compact non-sensitive model error summary."""
        status = getattr(getattr(exc, "response", None), "status_code", None)
        name = exc.__class__.__name__
        return f"{name}: HTTP {status}" if status else name

    def _status_from_errors(self, errors: list[str]) -> str:
        if not errors:
            return "LOCAL_MODEL_ERROR"
        unavailable_markers = ("ConnectError", "ConnectTimeout", "ReadTimeout")
        if any(any(marker in error for marker in unavailable_markers) for error in errors):
            return "LOCAL_MODEL_UNAVAILABLE"
        return "LOCAL_MODEL_ERROR"

    def _shrink_context(self, context: dict) -> dict:
        c = dict(context)
        c["relevant_evidence"] = c.get("relevant_evidence", [])[:2]
        c["state_summary"] = c.get("state_summary", "")[:800]
        return c
