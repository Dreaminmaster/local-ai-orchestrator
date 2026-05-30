"""Failure Handler — Diagnose and repair failures."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


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
            result.setdefault("can_auto_repair", False)
            result.setdefault("should_retry", True)
            return result
        except Exception as e:
            return {
                "failure_type": "tool_failure",
                "symptom": failure_info.get("error", "Unknown error"),
                "possible_causes": ["Unable to diagnose"],
                "repair_actions": [],
                "can_auto_repair": False,
                "should_retry": True,
                "max_retries": 2,
                "error": str(e),
            }
