"""Verifier — Check if task goals have been met with evidence."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage

SYSTEM_PROMPT = """你是一个任务验证器。你需要根据证据判断任务目标是否已经达成。
没有证据不能算完成；有报错不能算完成；必须逐条检查成功标准。"""

class Verifier:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def check_with_contracts(self, goal_contract: dict, authorization_contract: dict, results: list[dict], evidence: list[dict]) -> dict:
        """Verify success criteria from Goal Contract one by one."""
        criteria = goal_contract.get("success_criteria", [])
        context = f"""Goal Contract:
{json.dumps(goal_contract, ensure_ascii=False, indent=2)}

Authorization Contract:
{json.dumps(authorization_contract, ensure_ascii=False, indent=2)}

执行结果：
{json.dumps(results[-10:], ensure_ascii=False, indent=2)}

证据：
{json.dumps(evidence[-20:], ensure_ascii=False, indent=2)}

请逐条检查 success_criteria，输出 JSON：verified, criteria_results, missing_items, should_continue, next_actions, reason。"""
        try:
            result = await self.llm.chat_json([LLMMessage(role="system", content=SYSTEM_PROMPT), LLMMessage(role="user", content=context)], temperature=0.2)
            result.setdefault("verified", False)
            result.setdefault("missing_items", [])
            result.setdefault("should_continue", not result.get("verified", False))
            result.setdefault("next_actions", [])
            return result
        except Exception as e:
            evidence_text = json.dumps(evidence, ensure_ascii=False)
            criteria_results, missing = [], []
            for c in criteria:
                tokens = [w for w in str(c).replace('，',' ').replace('。',' ').split() if len(w) > 1]
                passed = bool(evidence) and (not tokens or any(w in evidence_text for w in tokens[:3]))
                criteria_results.append({"criterion": c, "passed": passed})
                if not passed:
                    missing.append(c)
            verified = bool(criteria) and not missing and any(r.get("success") for r in results)
            return {
                "verified": verified,
                "criteria_results": criteria_results,
                "missing_items": missing,
                "should_continue": bool(missing),
                "next_actions": ["continue_execution"] if missing else [],
                "reason": "heuristic contract verification",
                "error": str(e),
            }

    async def check(self, goal: dict, results: list[dict], evidence: list[dict]) -> dict:
        """Backward-compatible verification method."""
        goal_contract = goal.get("goal_contract") or {
            "final_goal": goal.get("main_goal", ""),
            "success_criteria": goal.get("success_criteria", []),
        }
        authorization_contract = goal.get("authorization_contract") or {}
        result = await self.check_with_contracts(goal_contract, authorization_contract, results, evidence)
        result.setdefault("next_action", "finish" if result.get("verified") else "continue")
        return result
