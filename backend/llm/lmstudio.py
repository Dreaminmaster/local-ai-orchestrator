"""LM Studio provider (wraps OpenAI-compatible)."""

from .openai_compat import OpenAICompatibleProvider


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio uses OpenAI-compatible API by default."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        super().__init__(
            base_url=base_url or "http://localhost:1234/v1",
            api_key="lm-studio",
            model=model or "local-model",
        )
