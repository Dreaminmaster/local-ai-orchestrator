"""Task Planner — Generate and dynamically adjust execution plans."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


SYSTEM_PROMPT = """你是一个任务规划器。根据目标和当前状态，生成可执行的步骤计划。

你必须输出严格的 JSON 格式：
{
  "plan": [
    {
      "step": 1,
      "goal": "这一步要做什么",
      "needed_skills": ["shell", "browser", "file", "external_ai", "visual_review", "search", "desktop", "self_verify"],
      "risk_level": "low/medium/high",
      "can_auto_execute": true
    }
  ],
  "total_steps": 4,
  "estimated_time": "5 minutes"
}

可用技能：
- shell: 执行终端命令
- file: 文件读写操作
- browser: 浏览器控制和网页操作
- desktop: 桌面控制（截图、点击等）
- external_ai: 调用外部 AI（ChatGPT/Claude/DeepSeek/Gemini）
- search: 搜索引擎
- visual_review: 视觉评审
- self_verify: 自我校验

规划原则：
1. 步骤要具体可执行
2. 不要一次写死所有步骤，留有动态调整空间
3. 每步都要有验证方式
4. 高风险动作标记 can_auto_execute: false
5. 考虑失败的备选方案"""


class TaskPlanner:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def create_plan(self, goal: dict, state: dict | None = None) -> dict:
        """Create an execution plan from a structured goal."""
        context = f"""目标信息：
{json.dumps(goal, ensure_ascii=False, indent=2)}

当前状态：
{json.dumps(state or {}, ensure_ascii=False, indent=2)}"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        try:
            result = await self.llm.chat_json(messages, temperature=0.3)
            result.setdefault("plan", [])
            result.setdefault("total_steps", len(result["plan"]))
            return result
        except Exception as e:
            # Fallback: single-step plan
            return {
                "plan": [{
                    "step": 1,
                    "goal": goal.get("main_goal", "Execute task"),
                    "needed_skills": ["shell"],
                    "risk_level": "low",
                    "can_auto_execute": True,
                }],
                "total_steps": 1,
                "error": str(e),
            }

    async def replan(self, goal: dict, state: dict, failure_info: dict) -> dict:
        """Re-plan after a failure."""
        context = f"""原始目标：
{json.dumps(goal, ensure_ascii=False, indent=2)}

当前状态：
{json.dumps(state, ensure_ascii=False, indent=2)}

失败信息：
{json.dumps(failure_info, ensure_ascii=False, indent=2)}

请根据失败信息重新规划后续步骤。"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        try:
            return await self.llm.chat_json(messages, temperature=0.3)
        except Exception:
            return {"plan": [], "total_steps": 0, "note": "Re-planning failed"}
