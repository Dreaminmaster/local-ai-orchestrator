"""Task Planner — local-model friendly short planning."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage

SYSTEM_PROMPT = """你是 local-ai-orchestrator 的任务规划器。
你面对的可能是较弱本地模型，所以必须遵守：
1. 不要长篇解释，只输出 JSON。
2. 只规划当前最有必要的少量步骤，通常 1-3 步。
3. 根据 Goal Contract 的 final_goal 和 success_criteria 规划。
4. 根据 Authorization Contract 的 granted_capabilities 选择技能。
5. 如果 full_autonomy 已授权，遇到困难要主动使用 external_ai / web_ai / search / visual_review / codex。
6. 每步必须包含 required_capabilities、verification_method、failure_fallback。

输出 JSON schema：
{
  "plan": [
    {
      "step": 1,
      "goal": "这一步要做什么",
      "needed_skills": ["browser", "visual_review"],
      "required_capabilities": ["operate_browser", "take_screenshots"],
      "verification_method": "如何验证这一步完成",
      "failure_fallback": "失败后怎么处理",
      "risk_level": "low",
      "can_auto_execute": true
    }
  ],
  "total_steps": 1
}

可用 skills：shell,file,browser,desktop,desktop_visual,external_ai,web_ai,search,visual_review,codex,memory,self_verify。"""

class TaskPlanner:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def create_plan(self, goal: dict, state: dict | None = None) -> dict:
        context = {
            "goal_contract": goal.get("goal_contract") or goal,
            "authorization_contract": (state or {}).get("authorization_contract") or goal.get("authorization_contract") or {},
            "current_state": state or {},
        }
        messages = [LLMMessage(role="system", content=SYSTEM_PROMPT), LLMMessage(role="user", content=json.dumps(context, ensure_ascii=False, indent=2))]
        try:
            result = await self.llm.chat_json(messages, temperature=0.2, max_tokens=1800)
            result.setdefault("plan", [])
            result.setdefault("total_steps", len(result["plan"]))
            return result
        except Exception as e:
            return self._fallback_plan(goal, state, str(e))

    def _fallback_plan(self, goal: dict, state: dict | None, error: str) -> dict:
        auth = (state or {}).get("authorization_contract") or goal.get("authorization_contract") or {}
        caps = set(auth.get("granted_capabilities", []))
        skills = ["self_verify"]
        req = []
        if "read_files" in caps:
            skills.insert(0, "file"); req.append("read_files")
        elif "operate_browser" in caps:
            skills.insert(0, "browser"); req.append("operate_browser")
        elif "ask_external_ai" in caps:
            skills.insert(0, "external_ai"); req.append("ask_external_ai")
        return {
            "plan": [{
                "step": 1,
                "goal": goal.get("main_goal") or goal.get("final_goal") or "Execute next minimal step",
                "needed_skills": skills,
                "required_capabilities": req,
                "verification_method": "check evidence and success criteria",
                "failure_fallback": "use external_ai or ask for clarification",
                "risk_level": "low",
                "can_auto_execute": True,
            }],
            "total_steps": 1,
            "error": error,
        }

    async def replan(self, goal: dict, state: dict, failure_info: dict) -> dict:
        state = dict(state or {})
        state["failure_info"] = failure_info
        return await self.create_plan(goal, state)
