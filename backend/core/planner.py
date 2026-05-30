"""Task Planner — local-model optimized short planning."""
from __future__ import annotations
from backend.llm.base import LLMProvider
from backend.local_model.local_model_runner import LocalModelRunner
from backend.local_model.prompt_builder import ContractScopedPromptBuilder

PLAN_SCHEMA = {
    "plan": [{
        "step": 1,
        "goal": "这一步要做什么",
        "needed_skills": ["browser", "visual_review"],
        "required_capabilities": ["operate_browser", "take_screenshots"],
        "verification_method": "如何验证这一步完成",
        "failure_fallback": "失败后怎么处理",
        "risk_level": "low",
        "can_auto_execute": True,
    }],
    "total_steps": 1,
}

class TaskPlanner:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.prompt_builder = ContractScopedPromptBuilder()
        self.local_model_runner = LocalModelRunner(llm)

    async def create_plan_from_optimized_context(self, optimized_context: dict) -> dict:
        fallback = self._fallback_plan_from_context(optimized_context, "local_model_fallback")
        def build_prompt(ctx, schema, attempt=0):
            if attempt > 0:
                ctx = dict(ctx)
                ctx["relevant_evidence"] = ctx.get("relevant_evidence", [])[:2]
                ctx["state_summary"] = ctx.get("state_summary", "")[:800]
            return self.prompt_builder.build_planner_prompt(ctx, schema)
        result = await self.local_model_runner.run_json(
            build_prompt=build_prompt,
            context=optimized_context,
            output_schema=PLAN_SCHEMA,
            fallback=fallback,
            escalation_reason="planner_uncertain",
        )
        result.setdefault("plan", [])
        result.setdefault("total_steps", len(result["plan"]))
        return result

    async def create_plan(self, goal: dict, state: dict | None = None) -> dict:
        context = {
            "goal_contract": goal.get("goal_contract") or goal,
            "authorization_contract": (state or {}).get("authorization_contract") or goal.get("authorization_contract") or {},
            "current_step": {},
            "state_summary": str(state or {})[:1500],
            "relevant_evidence": [],
            "available_skills": [],
        }
        return await self.create_plan_from_optimized_context(context)

    def _fallback_plan_from_context(self, context: dict, error: str) -> dict:
        goal = context.get("goal_contract", {})
        auth = context.get("authorization_contract", {})
        caps = set(auth.get("granted_capabilities", []))
        skills, req = ["self_verify"], []
        if "read_files" in caps:
            skills.insert(0, "file"); req.append("read_files")
        elif "operate_browser" in caps:
            skills.insert(0, "browser"); req.append("operate_browser")
        elif "ask_external_ai" in caps:
            skills.insert(0, "external_ai"); req.append("ask_external_ai")
        return {"plan": [{"step": 1, "goal": goal.get("final_goal") or "Execute next minimal step", "needed_skills": skills, "required_capabilities": req, "verification_method": "check evidence and success criteria", "failure_fallback": "use external_ai or ask for clarification", "risk_level": "low", "can_auto_execute": True}], "total_steps": 1, "error": error}

    def _fallback_plan(self, goal: dict, state: dict | None, error: str) -> dict:
        return self._fallback_plan_from_context({"goal_contract": goal, "authorization_contract": (state or {}).get("authorization_contract", {})}, error)

    async def replan(self, goal: dict, state: dict, failure_info: dict) -> dict:
        state = dict(state or {})
        state["failure_info"] = failure_info
        return await self.create_plan(goal, state)

    def convert_repair_actions_to_steps(self, repair_actions: list) -> list[dict]:
        steps=[]
        for i, action in enumerate(repair_actions, 1):
            name = action if isinstance(action, str) else action.get("action", str(action))
            lower = name.lower()
            if "codex" in lower or "code" in lower or "fix" in lower:
                skills=["codex", "file"]
                caps=["modify_code", "write_files"]
            elif "screenshot" in lower or "desktop" in lower or "selector" in lower:
                skills=["desktop_visual"]
                caps=["operate_desktop", "take_screenshots"]
            elif "external" in lower or "ai" in lower or "ask" in lower:
                skills=["external_ai"]
                caps=["ask_external_ai"]
            elif "search" in lower:
                skills=["search"]
                caps=[]
            else:
                skills=["self_verify"]
                caps=[]
            steps.append({"step": i, "goal": name, "needed_skills": skills, "required_capabilities": caps, "verification_method": "repair action produces evidence", "failure_fallback": "escalate or ask user", "risk_level": "medium" if caps else "low", "can_auto_execute": True})
        return steps
