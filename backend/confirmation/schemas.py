from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

@dataclass
class ConfirmationRequest:
    action: str
    risk_level: str
    reason: str
    payload: dict
    id: str = field(default_factory=lambda: str(uuid4())[:12])
    task_id: str | None = None
    step_id: str | None = None
    skill: str | None = None
    instruction: str | None = None
    context: dict = field(default_factory=dict)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
