from .quality_gates import QualityGates


class GoalVerifier:
    def __init__(self):
        self.gates = QualityGates()

    def verify(self, goal: dict, results: list[dict], evidence: list[dict]) -> dict:
        gates = [self.gates.evidence_gate(evidence), self.gates.code_gate(results)]
        passed = all(g.passed for g in gates)
        return {
            "verified": passed,
            "gates": [g.__dict__ for g in gates],
            "reason": "; ".join(g.reason for g in gates),
        }
