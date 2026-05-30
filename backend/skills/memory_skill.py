"""Memory Skill — Read/write task memory and user preference notes."""

from __future__ import annotations
from .base import Skill, SkillResult, RiskLevel


class MemorySkill(Skill):
    name = "memory"
    description = "Manage task memory and user preference notes"
    capabilities = ["remember", "recall", "preference_note"]
    risk_level = RiskLevel.LOW

    def __init__(self):
        self.memory: dict[str, list[str]] = {}

    async def can_handle(self, task: dict, state: dict) -> bool:
        desc = task.get("description", "").lower()
        return any(k in desc for k in ["remember", "memory", "preference", "recall"])

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "remember")
        task_id = context.get("task_id", "default")
        if action == "recall":
            items = self.memory.get(task_id, [])
            return SkillResult(
                skill=self.name,
                success=True,
                result="\n".join(items),
                metadata={"count": len(items)},
            )
        value = context.get("value", instruction)
        self.memory.setdefault(task_id, []).append(value)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Remembered: {value}",
            metadata={"task_id": task_id},
        )
