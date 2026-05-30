"""Failure Handler — Diagnose and repair failures."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage
from backend.core.repair_planner import RepairPlanner


SYSTEM_PROMPT = """你是一个失败处理器。分析失败原因并提出修复方案。

你必须输出严格的 JSON 格式：
{
  "failure_type": "tool_failure/login_failure/network_failure/ui_failure/code_failure/quality_failure/permission_failure",
  "symptom": "失败症状",
  "possible_causes": ["可能原因1", "可能原因2"],
  "repair_actions": [
    {
      "action": "修复动作描述",
      "skill": "需要使用的技能",
      "context": {},
      "priority": 1
    }
  ],
  "can_auto_repair": true/false,
  "should_retry": true/false,
  "max_retries": 3
}

失败类型：
- tool_failure: 工具执行失败
- login_failure: 登录失效
- network_failure: 网络失败
- ui_failure: 界面变化
- code_failure: 代码报错
- quality_failure: 结果质量不达标
- permission_failure: 权限不足"""


class FailureHandler:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.repair_planner = RepairPlanner()

    async def diagnose(self, failure_info: dict, state: dict) -> dict:
        """Diagnose a failure and suggest repairs."""
        context = f"""失败信息：
{json.dumps(failure_info, ensure_ascii=False, indent=2)}

当前状态：
{json.dumps(state, ensure_ascii=False, indent=2)}"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        try:
            result = await self.llm.chat_json(messages, temperature=0.3)
            fallback_plan = self.repair_planner.plan(
                failure_info.get("error", "") + json.dumps(failure_info, ensure_ascii=False),
                state.get("goal_contract"),
                state.get("authorization_contract"),
            )
            result.setdefault("failure_type", fallback_plan["failure_type"])
            result.setdefault("repair_plan", fallback_plan)
            result.setdefault("can_auto_repair", fallback_plan.get("should_retry", False))
            result.setdefault("should_retry", fallback_plan.get("should_retry", True))
            return result
        except Exception as e:
            plan = self.repair_planner.plan(failure_info.get("error", "Unknown error"), state.get("goal_contract"), state.get("authorization_contract"))
            return {
                "failure_type": plan["failure_type"],
                "symptom": failure_info.get("error", "Unknown error"),
                "possible_causes": ["Heuristic taxonomy diagnosis"],
                "repair_actions": plan["repair_actions"],
                "repair_plan": plan,
                "can_auto_repair": plan.get("should_retry", False),
                "should_retry": plan.get("should_retry", True),
                "max_retries": 2,
                "error": str(e),
            }
