"""OpenAI-compatible LLM provider (works with LM Studio, vLLM, llama.cpp, etc.)."""
from __future__ import annotations
import os
import httpx
from .base import LLMProvider, LLMMessage, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """Connects to any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "lm-studio")
        self.model = model or os.getenv("LLM_MODEL", "local-model")

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"].get("content", ""),
            raw=data,
            tool_calls=choice["message"].get("tool_calls", []),
        )
