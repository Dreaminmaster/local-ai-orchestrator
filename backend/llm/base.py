"""LLM Provider — Base interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str

@dataclass
class LLMResponse:
    content: str
    raw: dict = field(default_factory=dict)
    tool_calls: list[dict] = field(default_factory=list)

class LLMProvider(ABC):
    """Abstract base for all LLM backends."""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> LLMResponse:
        ...

    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """Chat and parse response as JSON using local-model tolerant repair."""
        from backend.local_model.json_repair import JSONRepairParser
        resp = await self.chat(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
        parsed = JSONRepairParser().parse(resp.content)
        if parsed:
            return parsed
        raise ValueError(f"Failed to parse JSON from model output: {resp.content[:500]}")
