"""Verifier — Check if task goals have been met with evidence."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


SYSTEM_PROMPT = """你是一个任务验证器。你需要根据证据判断任务目标是否已经达成。

你必须输出严格的 JSON 格式：
{
  "verified": true/false,
  "confidence": 0.85,
  "reason": "验证结论的原因",
  "evidence_summary": "证据总结",
  "unmet_criteria": ["未满足的标准1"],
  "next_action": "continue/finish/need_user",
  "suggestions": ["建议1"]
}

验证原则：
1. 没有证据不能算完成
2. 有报错不能算完成
3. 视觉任务需要截图证据
4. 代码任务需要运行成功的证据
5. 信息任务需要来源"""


class Verifier:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def check(self, goal: dict, results: list[dict], evidence: list[dict]) -> dict:
        """Verify if the goal has been achieved based on results and evidence."""
        context = f"""任务目标：
{json.dumps(goal, ensure_ascii=False, indent=2)}

执行结果：
{json.dumps(results[-3:] if len(results) > 3 else results, ensure_ascii=False, indent=2)}

收集的证据：
{json.dumps(evidence[-5:] if len(evidence) > 5 else evidence, ensure_ascii=False, indent=2)}"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        try:
            result = await self.llm.chat_json(messages, temperature=0.2)
            result.setdefault("verified", False)
            result.setdefault("next_action", "continue")
            return result
        except Exception as e:
            # Simple heuristic verification
            all_success = all(r.get("success", False) for r in results)
            return {
                "verified": all_success,
                "confidence": 0.5,
                "reason": "Heuristic: all steps succeeded" if all_success else "Some steps failed",
                "next_action": "finish" if all_success else "continue",
                "error": str(e),
            }
