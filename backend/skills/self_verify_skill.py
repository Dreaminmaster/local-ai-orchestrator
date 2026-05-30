"""Self Verify Skill — Verify task completion with evidence."""
from __future__ import annotations
import json
from .base import Skill, SkillResult, VerificationResult, RiskLevel


class SelfVerifySkill(Skill):
    name = "self_verify"
    description = "Verify whether a task step has been successfully completed"
    capabilities = [
        "verify_code_runs", "verify_file_exists", "verify_no_errors",
        "verify_visual_quality", "verify_information_accuracy",
    ]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["verify", "check", "confirm", "validate", "test"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        verification_type = context.get("verification_type", "general")
        evidence = context.get("evidence", [])
        success_criteria = context.get("success_criteria", [])

        checks = []
        all_passed = True

        # Check based on verification type
        if verification_type == "code_execution":
            checks = await self._verify_code(context)
        elif verification_type == "file_operation":
            checks = await self._verify_files(context)
        elif verification_type == "visual_quality":
            checks = await self._verify_visual(context)
        elif verification_type == "general":
            checks = await self._verify_general(context)

        all_passed = all(c["passed"] for c in checks)
        failed = [c for c in checks if not c["passed"]]

        result_summary = {
            "verified": all_passed,
            "checks": checks,
            "passed_count": sum(1 for c in checks if c["passed"]),
            "total_count": len(checks),
            "failed_items": [c["description"] for c in failed],
        }

        return SkillResult(
            skill=self.name,
            success=all_passed,
            result=json.dumps(result_summary, ensure_ascii=False, indent=2),
            evidence=evidence,
            needs_follow_up=not all_passed,
            suggested_next_action="fix_failures" if not all_passed else None,
            metadata=result_summary,
        )

    async def _verify_code(self, context: dict) -> list[dict]:
        checks = []
        # Check exit code
        exit_code = context.get("exit_code")
        if exit_code is not None:
            checks.append({
                "description": "Process exit code is 0",
                "passed": exit_code == 0,
                "evidence": f"exit_code={exit_code}",
            })
        # Check for error keywords in output
        output = context.get("output", "")
        error_keywords = ["error", "traceback", "exception", "failed", "fatal"]
        has_errors = any(kw in output.lower() for kw in error_keywords)
        checks.append({
            "description": "No error keywords in output",
            "passed": not has_errors,
            "evidence": f"Output contains error keywords: {has_errors}",
        })
        return checks

    async def _verify_files(self, context: dict) -> list[dict]:
        from pathlib import Path
        checks = []
        expected_files = context.get("expected_files", [])
        for f in expected_files:
            exists = Path(f).exists()
            checks.append({
                "description": f"File exists: {f}",
                "passed": exists,
                "evidence": f"exists={exists}",
            })
        return checks

    async def _verify_visual(self, context: dict) -> list[dict]:
        checks = []
        score = context.get("visual_score", 0)
        threshold = context.get("visual_threshold", 7.0)
        checks.append({
            "description": f"Visual score >= {threshold}",
            "passed": score >= threshold,
            "evidence": f"score={score}",
        })
        return checks

    async def _verify_general(self, context: dict) -> list[dict]:
        checks = []
        criteria = context.get("success_criteria", [])
        evidence_items = context.get("evidence", [])
        for criterion in criteria:
            # Simple check: criterion is met if there's any evidence
            checks.append({
                "description": criterion,
                "passed": len(evidence_items) > 0,
                "evidence": f"Evidence count: {len(evidence_items)}",
            })
        if not checks:
            checks.append({
                "description": "At least one evidence item exists",
                "passed": len(evidence_items) > 0,
                "evidence": f"Evidence count: {len(evidence_items)}",
            })
        return checks
