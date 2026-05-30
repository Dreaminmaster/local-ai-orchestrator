from dataclasses import dataclass


@dataclass
class ActionRisk:
    risk_level: str
    requires_confirmation: bool
    reason: str


class ActionRiskClassifier:
    HIGH_SKILLS = {"shell", "file", "codex", "desktop", "desktop_visual"}

    def classify(
        self,
        skill_name: str,
        instruction: str,
        context: dict,
        authorization_contract: dict,
    ) -> ActionRisk:
        mode = authorization_contract.get("authorization_mode", "standard")
        caps = set(authorization_contract.get("granted_capabilities", []))
        text = (instruction + " " + str(context)).lower()
        risk = "low"
        reason = "low-risk action"
        if skill_name in self.HIGH_SKILLS:
            risk = "medium"
            reason = f"{skill_name} can change local state"
        if any(
            x in text
            for x in [
                "delete",
                "rm ",
                "overwrite",
                "git push",
                "send",
                "upload",
                "payment",
                "付款",
            ]
        ):
            risk = "high"
            reason = "potentially destructive or external side-effect action"
        if skill_name == "shell" and "run_shell" not in caps:
            return ActionRisk("high", True, "run_shell not granted")
        if mode == "full_autonomy":
            return ActionRisk(risk, False, reason + "; full autonomy granted")
        return ActionRisk(risk, risk in ["medium", "high", "critical"], reason)
