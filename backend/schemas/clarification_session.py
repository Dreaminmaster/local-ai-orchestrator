from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
from uuid import uuid4
from datetime import datetime

class ClarificationQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    question: str
    reason: str = ""
    required: bool = True

class ClarificationAnswer(BaseModel):
    question_id: str
    answer: str

class ClarificationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:12])
    original_input: str
    goal_mode: Literal['clarify_first','autonomous'] = 'clarify_first'
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    answers: list[ClarificationAnswer] = Field(default_factory=list)
    status: Literal['pending','answered','contract_generated'] = 'pending'
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
