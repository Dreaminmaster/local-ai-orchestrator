from dataclasses import dataclass


@dataclass
class QualityGateResult:
    name: str
    passed: bool
    reason: str


class QualityGates:
    def code_gate(self, results: list[dict]) -> QualityGateResult:
        failed = [r for r in results if r.get("error")]
        return QualityGateResult(
            "code_gate",
            not failed,
            "no execution errors" if not failed else f"{len(failed)} errors",
        )

    def evidence_gate(self, evidence: list[dict]) -> QualityGateResult:
        return QualityGateResult(
            "evidence_gate", len(evidence) > 0, f"{len(evidence)} evidence items"
        )

    def visual_gate(self, review: dict | None) -> QualityGateResult:
        if not review:
            return QualityGateResult("visual_gate", False, "no visual review")
        return QualityGateResult(
            "visual_gate",
            bool(review.get("pass_gate") or review.get("pass")),
            str(review),
        )
