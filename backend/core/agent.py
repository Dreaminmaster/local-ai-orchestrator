"""Agent — The main orchestration loop that ties everything together."""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator

from backend.llm.base import LLMProvider, LLMMessage
from backend.llm.openai_compat import OpenAICompatibleProvider
from backend.llm.ollama import OllamaProvider
from backend.llm.lmstudio import LMStudioProvider
from backend.core.goal_interpreter import GoalInterpreter
from backend.core.planner import TaskPlanner
from backend.core.capability_gap import CapabilityGapDetector
from backend.core.skill_router import SkillRouter
from backend.core.verifier import Verifier
from backend.core.failure_handler import FailureHandler
from backend.core.supervisor import Supervisor
from backend.core.reporter import Reporter
from backend.core.observer import Observer
from backend.evidence.board import EvidenceBoard
from backend.memory.task_memory import TaskMemory
from backend.memory.user_preferences import UserPreferences


def create_llm_provider() -> LLMProvider:
    """Create the appropriate LLM provider based on config."""
    provider = os.getenv("LLM_PROVIDER", "lmstudio")
    if provider == "ollama":
        return OllamaProvider()
    elif provider == "lmstudio":
        return LMStudioProvider()
    else:
        return OpenAICompatibleProvider()


class AgentEvent:
    """An event emitted during agent execution for real-time UI updates."""

    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data, "timestamp": self.timestamp}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class Agent:
    """
    The main agent loop implementing the self-supervised orchestration cycle:

    Understand Goal → Generate Criteria → Plan → Detect Gaps →
    Select Tools → Execute → Observe → Save Evidence → Verify →
    Handle Failures → Continue/Finish → Report
    """

    def __init__(self, db=None):
        self.llm = create_llm_provider()
        self.goal_interpreter = GoalInterpreter(self.llm)
        self.planner = TaskPlanner(self.llm)
        self.gap_detector = CapabilityGapDetector(self.llm)
        self.skill_router = SkillRouter()
        self.verifier = Verifier(self.llm)
        self.failure_handler = FailureHandler(self.llm)
        self.supervisor = Supervisor()
        self.reporter = Reporter(self.llm)
        self.observer = Observer()
        self.evidence_board = EvidenceBoard()
        self.task_memory = TaskMemory()
        self.user_prefs = UserPreferences(db)

    async def run(self, user_input: str) -> AsyncGenerator[AgentEvent, None]:
        """
        Execute a task from user input, yielding events for real-time updates.
        This is the core orchestration loop.
        """
        task_id = str(uuid.uuid4())[:12]

        # ── Phase 1: Understand the goal ──────────────────────────────────
        yield AgentEvent("phase", {"phase": "understanding", "message": "🎯 正在理解任务目标..."})

        goal = await self.goal_interpreter.interpret(user_input)
        yield AgentEvent("goal", {"goal": goal})

        self.task_memory.remember(task_id, "goal", json.dumps(goal, ensure_ascii=False))

        # ── Phase 2: Create execution plan ────────────────────────────────
        yield AgentEvent("phase", {"phase": "planning", "message": "📋 正在制定执行计划..."})

        plan = await self.planner.create_plan(goal)
        yield AgentEvent("plan", {"plan": plan})

        steps = plan.get("plan", [])
        if not steps:
            yield AgentEvent("error", {"message": "无法生成执行计划"})
            return

        # ── Phase 3: Execute loop ─────────────────────────────────────────
        all_results = []
        all_evidence = []
        loop_count = 0
        consecutive_failures = 0
        current_step_index = 0

        while current_step_index < len(steps):
            loop_count += 1
            step = steps[current_step_index]
            step_id = f"step_{current_step_index + 1}"

            yield AgentEvent("step_start", {
                "step": current_step_index + 1,
                "total": len(steps),
                "goal": step.get("goal", ""),
                "skills": step.get("needed_skills", []),
            })

            # ── 3a: Observe state and detect capability gaps ──
            state = self.observer.collect(
                task_id=task_id,
                recent_results=all_results[-3:],
                evidence_summary=self.evidence_board.get_summary(task_id),
            )
            yield AgentEvent("observer_state", {"state": state})

            yield AgentEvent("phase", {"phase": "gap_detection", "message": "🔍 检测能力缺口..."})
            gap = await self.gap_detector.detect(step, state)
            if gap.get("requires_help"):
                yield AgentEvent("gap_detected", {"gap": gap})

            # ── 3b: Select skill chain ──
            skill_chain = self.skill_router.select(step, gap)
            yield AgentEvent("skills_selected", {"chain": skill_chain})

            # ── 3c: Generate execution instruction ──
            instruction = await self._generate_instruction(goal, step, gap)

            # ── 3d: Execute skill chain ──
            yield AgentEvent("phase", {"phase": "executing", "message": f"⚡ 执行中: {step.get('goal', '')}"})

            context = {
                "task_id": task_id,
                "step": step,
                "goal": goal,
                "gap": gap,
                "previous_results": all_results[-3:],
            }

            chain_results = await self.skill_router.execute_chain(skill_chain, instruction, context)

            # ── 3e: Save evidence ──
            for r in chain_results:
                evidence_entries = self.evidence_board.save_from_result(task_id, step_id, r)
                all_evidence.extend(evidence_entries)
                all_results.append(r)

            # Check step success
            step_success = any(r.get("success") for r in chain_results)

            yield AgentEvent("step_result", {
                "step": current_step_index + 1,
                "success": step_success,
                "results": chain_results,
            })

            if step_success:
                consecutive_failures = 0
                current_step_index += 1
            else:
                consecutive_failures += 1
                yield AgentEvent("phase", {"phase": "failure_handling", "message": "🔧 处理失败..."})

                failure_info = {
                    "step": step,
                    "results": chain_results,
                    "error": next((r.get("error") for r in chain_results if r.get("error")), "Unknown"),
                }
                repair = await self.failure_handler.diagnose(failure_info, {"results": all_results})
                yield AgentEvent("failure_repair", {"repair": repair})

                if repair.get("can_auto_repair") and repair.get("should_retry"):
                    # Retry the same step
                    self.task_memory.remember(task_id, "retry", json.dumps(failure_info, ensure_ascii=False))
                else:
                    # Move to next step
                    current_step_index += 1

            # ── 3f: Supervisor decision ──
            task_state = {
                "loop_count": loop_count,
                "consecutive_failures": consecutive_failures,
                "verified": False,
                "pending_steps": len(steps) - current_step_index,
                "has_high_risk_action": step.get("risk_level") in ("high", "critical"),
            }
            decision = self.supervisor.decide(task_state)

            if decision == "stop":
                yield AgentEvent("stopped", {"reason": "Too many failures or loops"})
                break
            elif decision == "need_user":
                yield AgentEvent("need_user", {"reason": "High-risk action requires confirmation"})
                break

        # ── Phase 4: Verification ─────────────────────────────────────────
        yield AgentEvent("phase", {"phase": "verifying", "message": "✅ 验证执行结果..."})

        verification = await self.verifier.check(goal, all_results, all_evidence)
        yield AgentEvent("verification", {"result": verification})

        # ── Phase 5: Final Report ─────────────────────────────────────────
        yield AgentEvent("phase", {"phase": "reporting", "message": "📝 生成最终报告..."})

        report = await self.reporter.generate(
            task={"id": task_id, "user_input": user_input, **goal},
            steps=[{"index": i, **r} for i, r in enumerate(all_results)],
            evidence=all_evidence,
        )
        yield AgentEvent("report", {"report": report})

        yield AgentEvent("complete", {
            "task_id": task_id,
            "verified": verification.get("verified", False),
            "total_steps": len(all_results),
            "success_rate": sum(1 for r in all_results if r.get("success")) / max(len(all_results), 1),
        })

    async def run_with_contracts(self, goal_contract: dict, authorization_contract: dict) -> AsyncGenerator[AgentEvent, None]:
        """Run agent with explicit Goal Contract and Authorization Contract.

        This is the new two-dimensional strategy entrypoint:
        goal understanding strategy × execution authorization strategy.
        """
        task_id = str(uuid.uuid4())[:12]
        goal = {
            "raw_input": goal_contract.get("original_input", ""),
            "main_goal": goal_contract.get("final_goal", ""),
            "task_type": "contract_task",
            "implicit_needs": goal_contract.get("assumptions", []),
            "success_criteria": goal_contract.get("success_criteria", []),
            "goal_contract": goal_contract,
            "authorization_contract": authorization_contract,
        }

        yield AgentEvent("goal_contract", {"goal_contract": goal_contract})
        yield AgentEvent("authorization_contract", {"authorization_contract": authorization_contract})
        self.evidence_board.save(task_id, None, "goal_contract", "contract", json.dumps(goal_contract, ensure_ascii=False), "Goal Contract for task")
        self.evidence_board.save(task_id, None, "authorization_contract", "contract", json.dumps(authorization_contract, ensure_ascii=False), "Authorization Contract for task")

        yield AgentEvent("phase", {"phase": "planning", "message": "📋 基于 Goal Contract 制定执行计划..."})
        plan = await self.planner.create_plan(goal, {"authorization_contract": authorization_contract})
        yield AgentEvent("plan", {"plan": plan})
        steps = plan.get("plan", [])
        if not steps:
            yield AgentEvent("error", {"message": "无法生成执行计划"})
            return

        all_results, all_evidence = [], []
        loop_count = consecutive_failures = current_step_index = 0
        while current_step_index < len(steps):
            loop_count += 1
            step = steps[current_step_index]
            step_id = f"step_{current_step_index + 1}"
            yield AgentEvent("step_start", {"step": current_step_index + 1, "total": len(steps), "goal": step.get("goal", ""), "skills": step.get("needed_skills", [])})
            state = self.observer.collect(task_id=task_id, recent_results=all_results[-3:], evidence_summary=self.evidence_board.get_summary(task_id))
            state["goal_contract"] = goal_contract
            state["authorization_contract"] = authorization_contract
            yield AgentEvent("observer_state", {"state": state})
            gap = await self.gap_detector.detect(step, state)
            if gap.get("requires_help"):
                yield AgentEvent("gap_detected", {"gap": gap})
            skill_chain = self.skill_router.select(step, gap, authorization_contract)
            yield AgentEvent("skills_selected", {"chain": skill_chain})
            if not skill_chain or skill_chain == ["self_verify"]:
                yield AgentEvent("permission_blocked", {"step": step, "reason": "Authorization Contract does not grant required capabilities"})
            instruction = await self._generate_instruction(goal, step, gap)
            context = {"task_id": task_id, "step": step, "goal": goal, "goal_contract": goal_contract, "authorization_contract": authorization_contract, "gap": gap, "previous_results": all_results[-3:]}
            chain_results = await self.skill_router.execute_chain(skill_chain, instruction, context)
            for r in chain_results:
                if authorization_contract.get("authorization_mode") == "full_autonomy" and r.get("metadata", {}).get("autonomous_actions"):
                    ev = self.evidence_board.save(task_id, step_id, "autonomous_action", "skill_router", json.dumps(r.get("metadata", {}).get("autonomous_actions"), ensure_ascii=False), "Full autonomy action executed within granted capabilities")
                    all_evidence.append(ev)
                evidence_entries = self.evidence_board.save_from_result(task_id, step_id, r)
                all_evidence.extend(evidence_entries)
                all_results.append(r)
            step_success = any(r.get("success") for r in chain_results)
            yield AgentEvent("step_result", {"step": current_step_index + 1, "success": step_success, "results": chain_results})
            if step_success:
                consecutive_failures = 0
                current_step_index += 1
            else:
                consecutive_failures += 1
                failure_info = {"step": step, "results": chain_results, "goal_contract": goal_contract, "authorization_contract": authorization_contract, "error": next((r.get("error") for r in chain_results if r.get("error")), "Unknown")}
                repair = await self.failure_handler.diagnose(failure_info, state)
                yield AgentEvent("failure_repair", {"repair": repair})
                if not (authorization_contract.get("execution_policy", {}).get("autonomous_retry") and repair.get("should_retry")):
                    current_step_index += 1
            decision = self.supervisor.decide({"loop_count": loop_count, "consecutive_failures": consecutive_failures, "verified": False, "pending_steps": len(steps)-current_step_index, "has_high_risk_action": step.get("risk_level") in ("high", "critical") and authorization_contract.get("authorization_mode") != "full_autonomy"})
            if decision in ("stop", "need_user"):
                yield AgentEvent(decision, {"reason": "Supervisor decision based on contracts"})
                break

        verification = await self.verifier.check_with_contracts(goal_contract, authorization_contract, all_results, all_evidence)
        yield AgentEvent("verification", {"result": verification})
        report = await self.reporter.generate_with_contracts(goal_contract, authorization_contract, steps=[{"index": i, **r} for i, r in enumerate(all_results)], evidence=all_evidence)
        yield AgentEvent("report", {"report": report})
        yield AgentEvent("complete", {"task_id": task_id, "verified": verification.get("verified", False), "total_steps": len(all_results), "success_rate": sum(1 for r in all_results if r.get("success")) / max(len(all_results), 1)})

    async def _generate_instruction(self, goal: dict, step: dict, gap: dict) -> str:
        """Generate a specific instruction for skill execution."""
        messages = [
            LLMMessage(role="system", content="""根据任务目标和当前步骤，生成一条具体的执行指令。
指令要明确、可执行，包含必要的上下文信息。直接输出指令文本，不要包装。"""),
            LLMMessage(role="user", content=f"""目标: {goal.get('main_goal', '')}
当前步骤: {step.get('goal', '')}
能力缺口: {gap.get('gap_type', 'none')}
需要的技能: {step.get('needed_skills', [])}"""),
        ]
        try:
            resp = await self.llm.chat(messages, temperature=0.3, max_tokens=500)
            return resp.content
        except Exception:
            return step.get("goal", "Execute task")
