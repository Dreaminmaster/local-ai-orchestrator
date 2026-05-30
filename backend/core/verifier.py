"""Verifier — contract success criteria verification with local-model protection."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider
from backend.local_model.local_model_runner import LocalModelRunner
from backend.local_model.prompt_builder import ContractScopedPromptBuilder

VERIFY_SCHEMA = {
    "verified": False,
    "criteria_results": [{"criterion": "...", "passed": False, "evidence_ids": [], "reason": "..."}],
    "missing_items": [],
    "should_continue": True,
    "next_actions": [],
    "reason": "...",
}

class Verifier:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.runner = LocalModelRunner(llm)
        self.prompt_builder = ContractScopedPromptBuilder()

    async def check_with_contracts(self, goal_contract: dict, authorization_contract: dict, results: list[dict], evidence: list[dict]) -> dict:
        criteria = goal_contract.get("success_criteria", [])
        criterion_evidence_map = self._map_evidence(criteria, evidence)
        context = {
            "goal_contract": {"final_goal": goal_contract.get("final_goal"), "success_criteria": criteria},
            "authorization_contract": authorization_contract,
            "current_step": {"type": "final_verification"},
            "state_summary": json.dumps({"result_summaries": results[-8:]}, ensure_ascii=False)[:2000],
            "relevant_evidence": criterion_evidence_map,
            "available_skills": [],
        }
        fallback = self._heuristic_verify(criteria, criterion_evidence_map, results)
        def build_prompt(ctx, schema, attempt=0):
            return self.prompt_builder.build_verifier_prompt(ctx, schema)
        result = await self.runner.run_json(build_prompt, context, VERIFY_SCHEMA, fallback, escalation_reason="local_model_uncertain")
        result.setdefault("verified", False)
        result.setdefault("criteria_results", fallback["criteria_results"])
        result.setdefault("missing_items", fallback["missing_items"])
        result.setdefault("should_continue", bool(result.get("missing_items")))
        result.setdefault("next_actions", [])
        return result

    def _map_evidence(self, criteria: list, evidence: list[dict]) -> list[dict]:
        mapped=[]
        for c in criteria:
            tokens=[w for w in str(c).replace('，',' ').replace('。',' ').split() if len(w)>1]
            matches=[]
            for ev in evidence:
                text=json.dumps(ev, ensure_ascii=False)
                if not tokens or any(t in text for t in tokens[:4]):
                    matches.append({"id": ev.get("id"), "type": ev.get("type"), "source": ev.get("source"), "supports": ev.get("supports"), "content": ev.get("content", "")[:300]})
            mapped.append({"criterion": c, "evidence": matches[:5]})
        return mapped

    def _heuristic_verify(self, criteria: list, mapped: list[dict], results: list[dict]) -> dict:
        criteria_results=[]; missing=[]
        for item in mapped:
            passed=bool(item.get("evidence"))
            criteria_results.append({"criterion": item["criterion"], "passed": passed, "evidence_ids": [e.get("id") for e in item.get("evidence", [])], "reason": "evidence found" if passed else "no evidence"})
            if not passed: missing.append(item["criterion"])
        verified=bool(criteria) and not missing and any(r.get("success") for r in results)
        return {"verified": verified, "criteria_results": criteria_results, "missing_items": missing, "should_continue": bool(missing), "next_actions": ["continue_execution"] if missing else [], "reason": "heuristic verification"}

    async def check(self, goal: dict, results: list[dict], evidence: list[dict]) -> dict:
        goal_contract = goal.get("goal_contract") or {"final_goal": goal.get("main_goal", ""), "success_criteria": goal.get("success_criteria", [])}
        authorization_contract = goal.get("authorization_contract") or {}
        result = await self.check_with_contracts(goal_contract, authorization_contract, results, evidence)
        result.setdefault("next_action", "finish" if result.get("verified") else "continue")
        return result
