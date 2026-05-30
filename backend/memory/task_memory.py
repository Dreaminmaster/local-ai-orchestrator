"""Task Memory — Remember what happened during task execution."""
from __future__ import annotations


class TaskMemory:
    """Stores execution context within a single task."""

    def __init__(self):
        self._memory: dict[str, list[dict]] = {}

    def remember(self, task_id: str, key: str, value: str):
        self._memory.setdefault(task_id, []).append({"key": key, "value": value})

    def recall(self, task_id: str, key: str | None = None) -> list[dict]:
        entries = self._memory.get(task_id, [])
        if key:
            return [e for e in entries if e["key"] == key]
        return entries

    def get_context(self, task_id: str) -> str:
        """Get a text summary of task memory for LLM context."""
        entries = self._memory.get(task_id, [])
        if not entries:
            return "No previous context."
        lines = [f"- {e['key']}: {e['value']}" for e in entries[-20:]]
        return "\n".join(lines)
