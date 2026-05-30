from backend.security.permissions import PermissionPolicy
class RiskClassifier:
    def __init__(self): self.policy=PermissionPolicy()
    def classify(self, action: str, payload: dict):
        if action == "shell": return self.policy.assess_command(payload.get("command", ""))
        if action == "file": return self.policy.assess_file_action(payload.get("file_action", "read_file"), payload.get("path", ""))
        return self.policy._decision(self.policy.confirm_level, "Unknown action type")
