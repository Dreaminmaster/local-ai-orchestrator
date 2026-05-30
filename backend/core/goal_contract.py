from backend.schemas.goal_contract import GoalContract
from backend.llm.base import LLMProvider, LLMMessage
import json

class GoalContractBuilder:
    def __init__(self, llm: LLMProvider): self.llm=llm
    async def build(self, original_input: str, goal_mode: str='autonomous', clarification_answers: str='', user_constraints: list[str] | None=None) -> GoalContract:
        prompt=f"""根据用户输入生成 Goal Contract JSON。
字段：goal_mode, original_input, final_goal, assumptions, user_constraints, success_criteria, clarification_summary, user_confirmed_goal, style_preferences, completion_standard。
目标理解策略：{goal_mode}
用户输入：{original_input}
澄清回答：{clarification_answers}
"""
        try:
            data=await self.llm.chat_json([LLMMessage(role='user', content=prompt)], temperature=0.25)
        except Exception:
            data={}
        return GoalContract(
            goal_mode=goal_mode,
            original_input=original_input,
            final_goal=data.get('final_goal') or original_input,
            assumptions=data.get('assumptions') or (["自主补全目标和执行方案"] if goal_mode=='autonomous' else []),
            user_constraints=(user_constraints or []) + data.get('user_constraints', []),
            success_criteria=data.get('success_criteria') or ["完成用户目标", "有证据证明结果", "输出最终报告"],
            clarification_summary=data.get('clarification_summary') or clarification_answers,
            user_confirmed_goal=bool(data.get('user_confirmed_goal', goal_mode=='autonomous')),
            style_preferences=data.get('style_preferences') or [],
            completion_standard=data.get('completion_standard') or "满足成功标准并通过验证",
        )
