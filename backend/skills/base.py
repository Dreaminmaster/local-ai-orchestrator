"""Skill base class — unified interface for all skills."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"  # 读取信息、截图、搜索
    MEDIUM = "medium"  # 填写表单、运行命令、修改本地文件
    HIGH = "high"  # 删除文件、发送消息、提交代码
    CRITICAL = "critical"  # 金融交易、账户安全、隐私数据外发


@dataclass
class SkillResult:
    skill: str
    success: bool
    result: str
    evidence: list[str] = field(default_factory=list)
    error: str | None = None
    needs_follow_up: bool = False
    suggested_next_action: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "success": self.success,
            "result": self.result,
            "evidence": self.evidence,
            "error": self.error,
            "needs_follow_up": self.needs_follow_up,
            "suggested_next_action": self.suggested_next_action,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    verified: bool
    reason: str
    next_action: str | None = None


class Skill(ABC):
    """Base class for all skills."""

    name: str = "base_skill"
    description: str = "Base skill"
    capabilities: list[str] = []
    risk_level: RiskLevel = RiskLevel.LOW

    @abstractmethod
    async def can_handle(self, task: dict, state: dict) -> bool:
        """Check if this skill can handle the given task."""
        ...

    @abstractmethod
    async def execute(self, instruction: str, context: dict) -> SkillResult:
        """Execute the skill with given instruction and context."""
        ...

    async def verify(self, result: SkillResult, context: dict) -> VerificationResult:
        """Verify the skill execution result."""
        return VerificationResult(
            verified=result.success,
            reason="Default verification: success = verified",
        )
