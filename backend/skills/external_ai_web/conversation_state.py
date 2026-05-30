from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationState:
    provider: str
    profile: str
    url: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    prompts: list[str] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    evidence_files: list[str] = field(default_factory=list)
