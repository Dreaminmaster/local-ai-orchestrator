"""Action-level risk classifier.

Classifies concrete instructions, not just skill names.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActionRisk:
    risk_level: str
    reason: str
    requires_confirmation: bool


class ActionRiskClassifier:
    HIGH_PATTERNS = [
        "rm -rf",
        "delete",
        "remove",
        "git push",
        "publish",
        "send email",
        "upload",
        "payment",
        "secret",
        "token",
        "chmod -r",
        "sudo",
    ]
    MEDIUM_PATTERNS = [
        "write",
        "modify",
        "install",
        "pip install",
        "npm install",
        "run shell",
        "execute",
        "click",
        "type",
    ]

    def classify(
        self,
        skill_name: str,
        instruction: str,
        context: dict | None = None,
        authorization_contract: dict | None = None,
    ) -> ActionRisk:
        context = context or {}
        authorization_contract = authorization_contract or {}
        text = " ".join(
            [
                skill_name or "",
                instruction or "",
                str(context.get("command", "")),
                str(context.get("path", "")),
                str(context.get("step", {})),
            ]
        ).lower()
        mode = authorization_contract.get("authorization_mode", "standard")
        if any(p in text for p in self.HIGH_PATTERNS):
            return ActionRisk(
                "high",
                "Concrete instruction matches high-risk pattern",
                mode != "full_autonomy",
            )
        if any(p in text for p in self.MEDIUM_PATTERNS):
            return ActionRisk(
                "medium", "Concrete instruction modifies or controls environment", False
            )
        if skill_name in {"shell", "file", "desktop", "desktop_visual", "codex"}:
            return ActionRisk(
                "medium", f"{skill_name} can affect local environment", False
            )
        return ActionRisk("low", "Low-risk action", False)
