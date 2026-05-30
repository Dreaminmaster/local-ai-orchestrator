"""LLM Provider — Base interface."""
from __future__ import annotations
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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
        """Chat and parse response as JSON."""
        resp = await self.chat(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
        text = resp.content.strip()
        # Try to extract JSON from markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # Remove opening ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)
