"""Failure Handler — local-model protected failure diagnosis."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider
from backend.core.repair_planner import RepairPlanner
from backend.local_model.local_model_runner import LocalModelRunner
from backend.local_model.prompt_builder import ContractScopedPromptBuilder

FAILURE_SCHEMA = {
    "failure_type": "tool_failure",
    "symptom": "...",
    "possible_causes": [],
    "repair_actions": [],
    "can_auto_repair": False,
    "should_retry": True,
    "max_retries": 2,
}

class FailureHandler:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.repair_planner = RepairPlanner()
        self.runner = LocalModelRunner(llm)
        self.prompt_builder = ContractScopedPromptBuilder()

    async def diagnose(self, failure_info: dict, state: dict) -> dict:
        error = failure_info.get("error") or json.dumps(failure_info, ensure_ascii=False)[:1000]
        goal_contract = state.get("goal_contract") or failure_info.get("goal_contract") or {}
        authorization_contract = state.get("authorization_contract") or failure_info.get("authorization_contract") or {}
        fallback_plan = self.repair_planner.plan(error, goal_contract, authorization_contract)
        fallback = {
            "failure_type": fallback_plan["failure_type"],
            "symptom": error,
            "possible_causes": ["Heuristic taxonomy diagnosis"],
            "repair_actions": fallback_plan["repair_actions"],
            "repair_plan": fallback_plan,
            "can_auto_repair": fallback_plan.get("should_retry", False),
            "should_retry": fallback_plan.get("should_retry", True),
            "max_retries": 2,
        }
        context = state.get("optimized_context") or {
            "goal_contract": goal_contract,
            "authorization_contract": authorization_contract,
            "current_step": failure_info.get("step", {}),
            "state_summary": json.dumps(state, ensure_ascii=False)[:1200],
            "relevant_evidence": [],
            "available_skills": [],
        }
        def build_prompt(ctx, schema, attempt=0):
            return self.prompt_builder.build_failure_prompt(ctx, error, schema)
        result = await self.runner.run_json(build_prompt, context, FAILURE_SCHEMA, fallback, escalation_reason="local_model_uncertain")
        result.setdefault("failure_type", fallback_plan["failure_type"])
        result.setdefault("repair_actions", fallback_plan["repair_actions"])
        result.setdefault("repair_plan", fallback_plan)
        result.setdefault("should_retry", fallback_plan.get("should_retry", True))
        result.setdefault("can_auto_repair", fallback_plan.get("should_retry", False))
        return result
