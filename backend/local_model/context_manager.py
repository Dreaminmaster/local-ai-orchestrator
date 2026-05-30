from dataclasses import dataclass
from typing import List
import json

@dataclass
class ContextBudget:
    max_chars: int = 12000
    reserved_for_output: int = 2000
    max_evidence_items: int = 8
    max_recent_events: int = 10

class ContextWindowManager:
    def __init__(self, budget: ContextBudget | None = None):
        self.budget = budget or ContextBudget()
    def build_context(self, goal_contract: dict, authorization_contract: dict, current_step: dict, state_summary: str, relevant_evidence: List[dict], available_skills: List[dict]) -> dict:
        context = {
            'goal_contract': self._compress_goal_contract(goal_contract),
            'authorization_contract': self._compress_authorization_contract(authorization_contract),
            'current_step': current_step,
            'state_summary': state_summary[:2500],
            'relevant_evidence': relevant_evidence[: self.budget.max_evidence_items],
            'available_skills': available_skills,
        }
        return self._fit_budget(context)
    def _compress_goal_contract(self, data: dict) -> dict:
        return {
            'goal_mode': data.get('goal_mode'),
            'final_goal': data.get('final_goal'),
            'assumptions': data.get('assumptions', []),
            'user_constraints': data.get('user_constraints', []),
            'success_criteria': data.get('success_criteria', []),
            'completion_standard': data.get('completion_standard', ''),
        }
    def _compress_authorization_contract(self, data: dict) -> dict:
        return {
            'authorization_mode': data.get('authorization_mode'),
            'granted_capabilities': data.get('granted_capabilities', []),
            'available_external_ai': data.get('available_external_ai', []),
            'execution_policy': data.get('execution_policy', {}),
            'provided_resources': data.get('provided_resources', {}),
        }
    def _fit_budget(self, context: dict) -> dict:
        text = json.dumps(context, ensure_ascii=False)
        if len(text) <= self.budget.max_chars:
            return context
        context['state_summary'] = context.get('state_summary', '')[:1200]
        context['relevant_evidence'] = context.get('relevant_evidence', [])[:3]
        return context
