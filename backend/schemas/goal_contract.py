from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

GoalMode = Literal["clarify_first", "autonomous"]


class GoalContract(BaseModel):
    goal_mode: GoalMode = "autonomous"
    original_input: str
    final_goal: str
    assumptions: list[str] = Field(default_factory=list)
    user_constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_summary: str = ""
    user_confirmed_goal: bool = False
    style_preferences: list[str] = Field(default_factory=list)
    completion_standard: str = ""
