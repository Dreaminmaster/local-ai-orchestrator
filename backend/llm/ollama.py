"""Ollama LLM provider."""
from __future__ import annotations
import os
import httpx
from .base import LLMProvider, LLMMessage, LLMResponse


class OllamaProvider(LLMProvider):
    """Connects to Ollama's API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "llama3")

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
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            raw=data,
        )
