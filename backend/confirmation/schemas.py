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
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
