"""Goal Interpreter — Transform vague user input into structured goals."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


SYSTEM_PROMPT = """你是一个目标理解器。你的任务是把用户模糊的输入转化为结构化的任务目标。

你必须输出严格的 JSON 格式：
{
  "raw_input": "用户原始输入",
  "main_goal": "主要目标的一句话描述",
  "task_type": "任务类型",
  "implicit_needs": ["隐含需求1", "隐含需求2"],
  "success_criteria": ["完成标准1", "完成标准2"],
  "needed_capabilities": ["需要的能力1", "需要的能力2"],
  "estimated_complexity": "low/medium/high"
}

任务类型包括：
- code_fix: 修复代码问题
- code_create: 创建新代码
- design_improvement: 改善设计/UI
- research: 研究和分析
- automation: 自动化操作
- data_processing: 数据处理
- general: 通用任务

请仔细分析用户的真实意图，不要遗漏隐含需求。"""


class GoalInterpreter:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def interpret(self, user_input: str) -> dict:
        """Transform user input into structured goal."""
        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_input),
        ]

        try:
            result = await self.llm.chat_json(messages, temperature=0.3)
            # Ensure required fields
            result.setdefault("raw_input", user_input)
            result.setdefault("main_goal", user_input)
            result.setdefault("task_type", "general")
            result.setdefault("implicit_needs", [])
            result.setdefault("success_criteria", [])
            result.setdefault("needed_capabilities", [])
            result.setdefault("estimated_complexity", "medium")
            return result
        except Exception as e:
            # Fallback: basic interpretation
            return {
                "raw_input": user_input,
                "main_goal": user_input,
                "task_type": "general",
                "implicit_needs": [],
                "success_criteria": ["任务完成"],
                "needed_capabilities": [],
                "estimated_complexity": "medium",
                "error": str(e),
            }
