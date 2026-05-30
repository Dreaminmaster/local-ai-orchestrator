"""Risk and permission policy for agent actions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import os


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


@dataclass
class RiskAssessment:
    allowed: bool
    requires_confirmation: bool
    risk_level: RiskLevel
    reason: str


class PermissionPolicy:
    """Centralized safety policy.

    High-risk and critical actions must be confirmed by the user. The policy
    blocks obviously destructive operations by default even before confirmation.
    """

    destructive_patterns = [
        "rm -rf /",
        "rm -rf ~",
        "mkfs",
        "dd if=",
        ":(){ :|:& };:",
        "chmod -R 777 /",
        "chown -R",
        "shutdown",
        "reboot",
    ]

    sensitive_keywords = [
        "password",
        "secret",
        "token",
        "api_key",
        "private_key",
        "wallet",
        "payment",
    ]

    def __init__(self, confirm_level: str | None = None):
        raw = confirm_level or os.getenv("CONFIRM_RISK_LEVEL", "high")
        self.confirm_level = RiskLevel(raw)

    def assess_command(self, command: str) -> RiskAssessment:
        lower = command.lower()
        if any(p in lower for p in self.destructive_patterns):
            return RiskAssessment(False, True, RiskLevel.CRITICAL, "Command matches destructive pattern")
        if any(k in lower for k in ["git push", "sendmail", "curl -x post", "curl -d"]):
            return self._decision(RiskLevel.HIGH, "Command may publish or send data")
        if any(k in lower for k in ["rm ", "mv ", "chmod", "pip install", "npm install", "apk add"]):
            return self._decision(RiskLevel.MEDIUM, "Command modifies local environment")
        return self._decision(RiskLevel.LOW, "Read-only or low-risk command")

    def assess_file_action(self, action: str, path: str) -> RiskAssessment:
        lower_path = path.lower()
        if any(k in lower_path for k in self.sensitive_keywords):
            return self._decision(RiskLevel.HIGH, "Path may contain sensitive data")
        if action in {"delete_file", "delete_directory"}:
            return self._decision(RiskLevel.HIGH, "Delete operation")
        if action in {"write_file", "modify_file"}:
            return self._decision(RiskLevel.MEDIUM, "File modification")
        return self._decision(RiskLevel.LOW, "Read-only file operation")

    def _decision(self, risk: RiskLevel, reason: str) -> RiskAssessment:
        requires = RISK_ORDER[risk] >= RISK_ORDER[self.confirm_level]
        return RiskAssessment(True, requires, risk, reason)
