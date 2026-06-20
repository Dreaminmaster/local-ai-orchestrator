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
from backend.local_model.context_manager import ContextWindowManager
from backend.local_model.evidence_retriever import EvidenceRetriever
from backend.local_model.tool_result_summarizer import ToolResultSummarizer
from backend.local_model.step_state import StepStateManager
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter
from backend.local_model.step_state_store import StepStateStore
from backend.core.task_action_compiler import TaskActionCompiler
from backend.core.task_artifact_store import TaskArtifactStore
from backend.core.product_errors import product_error
from backend.skills.external_ai_web.pending_action import pending_external_ai_store
from backend.settings_store import SettingsStore


def create_llm_provider(role: str = "planner") -> LLMProvider:
    """Create a role-aware local provider from product settings, with env fallback."""
    settings = SettingsStore().load().get("local_models", {})
    role_value = str((settings.get("roles") or {}).get(role) or "")
    provider = str(settings.get("default_provider") or os.getenv("LLM_PROVIDER", "lmstudio"))
    model = str(settings.get("default_model") or "")
    if ":" in role_value:
        provider, model = role_value.split(":", 1)
    elif role_value:
        model = role_value
    config = settings.get(provider, {}) if provider in {"lmstudio", "ollama"} else {}
    if not config.get("enabled", True):
        fallback_provider = next(
            (
                name
                for name in ("lmstudio", "ollama")
                if settings.get(name, {}).get("enabled")
            ),
            provider,
        )
        provider = fallback_provider
        config = settings.get(provider, {})
    model = model or str(config.get("default_model") or "") or None
    endpoint = str(config.get("endpoint") or "").rstrip("/")
    if provider == "ollama":
        return OllamaProvider(base_url=endpoint or None, model=model)
    elif provider == "lmstudio":
        base_url = f"{endpoint}/v1" if endpoint and not endpoint.endswith("/v1") else endpoint
        return LMStudioProvider(base_url=base_url or None, model=model)
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
        self.llm = create_llm_provider("planner")
        self.goal_interpreter = GoalInterpreter(self.llm)
        self.planner = TaskPlanner(self.llm)
        self.gap_detector = CapabilityGapDetector(create_llm_provider("executor"))
        self.skill_router = SkillRouter()
        self.verifier = Verifier(create_llm_provider("verifier"))
        self.failure_handler = FailureHandler(create_llm_provider("repair"))
        self.supervisor = Supervisor()
        self.reporter = Reporter(create_llm_provider("summarizer"))
        self.observer = Observer()
        self.evidence_board = EvidenceBoard()
        self.task_memory = TaskMemory()
        self.user_prefs = UserPreferences(db)
        self.context_manager = ContextWindowManager()
        self.tool_summarizer = ToolResultSummarizer()
        self.step_state_manager = StepStateManager()
        self.escalation_router = ExternalAIEscalationRouter()
        self.step_state_store = StepStateStore()
        self.task_action_compiler = TaskActionCompiler()
        self.task_artifact_store = TaskArtifactStore()

    async def run(self, user_input: str) -> AsyncGenerator[AgentEvent, None]:
        """
        Execute a task from user input, yielding events for real-time updates.
        This is the core orchestration loop.
        """
        task_id = str(uuid.uuid4())[:12]

        # Phase 1: Understand the goal
        yield AgentEvent(
            "phase", {"phase": "understanding", "message": "🎯 正在理解任务目标..."}
        )

        goal = await self.goal_interpreter.interpret(user_input)
        yield AgentEvent("goal", {"goal": goal})

        self.task_memory.remember(task_id, "goal", json.dumps(goal, ensure_ascii=False))

        # Phase 2: Create execution plan
        yield AgentEvent(
            "phase", {"phase": "planning", "message": "📋 正在制定执行计划..."}
        )

        plan = await self.planner.create_plan(goal)
        yield AgentEvent("plan", {"plan": plan})

        steps = plan.get("plan", [])
        if not steps:
            yield AgentEvent("error", {"message": "无法生成执行计划"})
            return

        # Phase 3: Execute loop
        all_results = []
        all_evidence = []
        loop_count = 0
        consecutive_failures = 0
        current_step_index = 0

        while current_step_index < len(steps):
            loop_count += 1
            step = steps[current_step_index]
            step_id = f"step_{current_step_index + 1}"

            yield AgentEvent(
                "step_start",
                {
                    "step": current_step_index + 1,
                    "total": len(steps),
                    "goal": step.get("goal", ""),
                    "skills": step.get("needed_skills", []),
                },
            )

            # Step 3a: observe and detect gaps
            state = self.observer.collect(
                task_id=task_id,
                recent_results=all_results[-3:],
                evidence_summary=self.evidence_board.get_summary(task_id),
            )
            yield AgentEvent("observer_state", {"state": state})

            yield AgentEvent(
                "phase", {"phase": "gap_detection", "message": "🔍 检测能力缺口..."}
            )
            gap = await self.gap_detector.detect(step, state)
            if gap.get("requires_help"):
                yield AgentEvent("gap_detected", {"gap": gap})

            # Step 3b: select skill chain
            skill_chain = self.skill_router.select(step, gap)
            yield AgentEvent("skills_selected", {"chain": skill_chain})

            # Step 3c: generate instruction
            instruction = await self._generate_instruction(goal, step, gap)

            # Step 3d: execute skill chain
            yield AgentEvent(
                "phase",
                {"phase": "executing", "message": f"⚡ 执行中: {step.get('goal', '')}"},
            )

            context = {
                "task_id": task_id,
                "step": step,
                "goal": goal,
                "gap": gap,
                "previous_results": all_results[-3:],
            }

            chain_results = await self.skill_router.execute_chain(
                skill_chain, instruction, context
            )

            # Step 3e: save evidence
            for r in chain_results:
                evidence_entries = self.evidence_board.save_from_result(
                    task_id, step_id, r
                )
                all_evidence.extend(evidence_entries)
                all_results.append(r)

            # Check step success
            step_success = any(r.get("success") for r in chain_results)

            yield AgentEvent(
                "step_result",
                {
                    "step": current_step_index + 1,
                    "success": step_success,
                    "results": chain_results,
                },
            )

            if step_success:
                consecutive_failures = 0
                current_step_index += 1
            else:
                consecutive_failures += 1
                yield AgentEvent(
                    "phase", {"phase": "failure_handling", "message": "🔧 处理失败..."}
                )

                failure_info = {
                    "step": step,
                    "results": chain_results,
                    "error": next(
                        (r.get("error") for r in chain_results if r.get("error")),
                        "Unknown",
                    ),
                }
                repair = await self.failure_handler.diagnose(
                    failure_info, {"results": all_results}
                )
                yield AgentEvent("failure_repair", {"repair": repair})

                if repair.get("can_auto_repair") and repair.get("should_retry"):
                    # Retry the same step
                    self.task_memory.remember(
                        task_id, "retry", json.dumps(failure_info, ensure_ascii=False)
                    )
                else:
                    # Move to next step
                    current_step_index += 1

            # Step 3f: supervisor decision
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
                yield AgentEvent(
                    "need_user", {"reason": "High-risk action requires confirmation"}
                )
                break

        # Phase 4: Verification
        yield AgentEvent(
            "phase", {"phase": "verifying", "message": "✅ 验证执行结果..."}
        )

        verification = await self.verifier.check(goal, all_results, all_evidence)
        yield AgentEvent("verification", {"result": verification})

        # Phase 5: Final Report
        yield AgentEvent(
            "phase", {"phase": "reporting", "message": "📝 生成最终报告..."}
        )

        report = await self.reporter.generate(
            task={"id": task_id, "user_input": user_input, **goal},
            steps=[{"index": i, **r} for i, r in enumerate(all_results)],
            evidence=all_evidence,
        )
        yield AgentEvent("report", {"report": report})

        yield AgentEvent(
            "complete",
            {
                "task_id": task_id,
                "verified": verification.get("verified", False),
                "total_steps": len(all_results),
                "success_rate": sum(1 for r in all_results if r.get("success"))
                / max(len(all_results), 1),
            },
        )

    async def run_with_contracts(
        self, goal_contract: dict, authorization_contract: dict
    ) -> AsyncGenerator[AgentEvent, None]:
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
        self.task_artifact_store.initialize(task_id, goal_contract, authorization_contract)

        yield AgentEvent("goal_contract", {"goal_contract": goal_contract})
        yield AgentEvent(
            "authorization_contract", {"authorization_contract": authorization_contract}
        )
        self.evidence_board.save(
            task_id,
            None,
            "goal_contract",
            "contract",
            json.dumps(goal_contract, ensure_ascii=False),
            "Goal Contract for task",
        )
        self.evidence_board.save(
            task_id,
            None,
            "authorization_contract",
            "contract",
            json.dumps(authorization_contract, ensure_ascii=False),
            "Authorization Contract for task",
        )

        yield AgentEvent(
            "phase",
            {"phase": "planning", "message": "📋 基于压缩上下文制定执行计划..."},
        )
        initial_context = self.context_manager.build_context(
            goal_contract=goal_contract,
            authorization_contract=authorization_contract,
            current_step={"goal": goal_contract.get("final_goal", "initial planning")},
            state_summary="initial planning",
            relevant_evidence=self.evidence_board.get_task_evidence(task_id),
            available_skills=[
                {"name": k, "capabilities": v.capabilities}
                for k, v in self.skill_router.get_all_skills().items()
            ],
        )
        compiled_steps = self.task_action_compiler.compile(
            goal_contract, authorization_contract
        )
        structured_plan = bool(compiled_steps)
        if compiled_steps:
            plan = {
                "plan": compiled_steps,
                "total_steps": len(compiled_steps),
                "source": "structured_local_action_compiler",
                "local_model_status": "FALLBACK_USED",
                "fallback_used": True,
            }
        else:
            plan = await self.planner.create_plan_from_optimized_context(initial_context)
        self.task_artifact_store.save_plan(task_id, plan)
        self.task_artifact_store.update_state(
            task_id,
            status="planned",
            plan_source=plan.get("source", "local_model"),
            local_model_status=plan.get("local_model_status", "READY"),
            fallback_used=bool(plan.get("fallback_used")),
        )
        if plan.get("fallback_used"):
            model_status = plan.get("local_model_status", "LOCAL_MODEL_ERROR")
            model_message = (
                "本地模型不可用，已切换规则规划"
                if model_status == "LOCAL_MODEL_UNAVAILABLE"
                else "本地模型返回错误，已切换规则规划"
            )
            self.evidence_board.save(
                task_id,
                None,
                "local_model_status",
                "planner",
                plan.get("local_model_error_summary", model_status),
                model_message,
            )
            yield AgentEvent(
                "local_model_status",
                {
                    "status": model_status,
                    "fallback_used": True,
                    "message": model_message,
                },
            )
        yield AgentEvent("plan", {"plan": plan})
        steps = plan.get("plan", [])
        if not steps:
            yield AgentEvent("error", {"message": "无法生成执行计划"})
            return

        all_results, all_evidence = [], []
        self.step_state_manager.initialize_contracts(
            task_id, goal_contract, authorization_contract, steps
        )
        self.step_state_store.save(self.step_state_manager.get(task_id))
        loop_count = consecutive_failures = current_step_index = 0
        while current_step_index < len(steps):
            loop_count += 1
            step = steps[current_step_index]
            self.step_state_store.save(self.step_state_manager.get(task_id))
            step_id = f"step_{current_step_index + 1}"
            yield AgentEvent(
                "step_start",
                {
                    "task_id": task_id,
                    "step": current_step_index + 1,
                    "total": len(steps),
                    "goal": step.get("goal", ""),
                    "skills": step.get("needed_skills", []),
                },
            )
            self.task_artifact_store.update_state(
                task_id,
                status="running",
                current_step=current_step_index + 1,
                total_steps=len(steps),
            )
            self.task_artifact_store.append_step_log(
                task_id,
                {
                    "type": "step_start",
                    "step": current_step_index + 1,
                    "goal": step.get("goal", ""),
                    "skills": step.get("needed_skills", []),
                },
            )
            state = self.observer.collect(
                task_id=task_id,
                recent_results=all_results[-3:],
                evidence_summary=self.evidence_board.get_summary(task_id),
            )
            state["goal_contract"] = goal_contract
            state["authorization_contract"] = authorization_contract
            step_state = self.step_state_manager.get(task_id)
            retriever = EvidenceRetriever(self.evidence_board)
            relevant_evidence = retriever.retrieve_for_step(task_id, step)
            optimized_context = self.context_manager.build_context(
                goal_contract=goal_contract,
                authorization_contract=authorization_contract,
                current_step=step,
                state_summary=json.dumps(
                    {"observer": state, "step_state": step_state.__dict__},
                    ensure_ascii=False,
                ),
                relevant_evidence=relevant_evidence,
                available_skills=[
                    {"name": k, "capabilities": v.capabilities}
                    for k, v in self.skill_router.get_all_skills().items()
                ],
            )
            state["optimized_context"] = optimized_context
            yield AgentEvent("optimized_context", {"context": optimized_context})
            yield AgentEvent("observer_state", {"state": state})
            gap = (
                {"requires_help": False, "gap_type": "none"}
                if step.get("structured_action")
                else await self.gap_detector.detect(step, state)
            )
            if gap.get("requires_help"):
                yield AgentEvent("gap_detected", {"gap": gap})
            skill_chain = self.skill_router.select(step, gap, authorization_contract)
            yield AgentEvent("skills_selected", {"chain": skill_chain})
            if not skill_chain or skill_chain == ["self_verify"]:
                yield AgentEvent(
                    "permission_blocked",
                    {
                        "step": step,
                        "reason": "Authorization Contract does not grant required capabilities",
                    },
                )
            instruction = await self._generate_instruction(goal, step, gap)
            context = {
                "task_id": task_id,
                "step_index": current_step_index,
                "step": step,
                "goal": goal,
                "goal_contract": goal_contract,
                "authorization_contract": authorization_contract,
                "gap": gap,
                "previous_results": all_results[-3:],
            }
            context.update(
                self._materialize_tool_context(
                    step, authorization_contract, all_results
                )
            )
            if context.get("pending_external_ai_mock"):
                pending = pending_external_ai_store.save(
                    task_id=task_id,
                    step_id=step_id,
                    provider="claude",
                    original_prompt=goal_contract.get("original_input", ""),
                    redacted_prompt="[simulated pending external AI prompt]",
                    context={"simulation": True},
                    provider_status="NEED_LOGIN",
                    failure_reason="pending_external_ai_mock",
                    suggested_user_action="Open Claude Workspace and log in, then click Recheck/Resume",
                )
                self.task_artifact_store.update_state(
                    task_id,
                    status="needs_user",
                    failure_reason="pending_external_ai_mock",
                    product_error=product_error(
                        "EXTERNAL_AI_NEED_LOGIN", detail="pending_external_ai_mock"
                    ),
                    pending_external_ai=True,
                )
                yield AgentEvent(
                    "external_ai_need_user",
                    {
                        "task_id": task_id,
                        "provider": "claude",
                        "reason": "pending_external_ai_mock",
                        "suggested_user_action": pending.get("suggested_user_action"),
                    },
                )
                yield AgentEvent(
                    "external_ai_pending_saved",
                    {"task_id": task_id, "pending": pending},
                )
                yield AgentEvent(
                    "stopped",
                    {
                        "task_id": task_id,
                        "reason": "external_ai_need_user",
                        "status": "needs_user",
                        "resume_payload": {"task_id": task_id, "resume_from_task_id": task_id},
                    },
                )
                return
            chain_results = await self.skill_router.execute_chain(
                skill_chain, instruction, context
            )
            pending_external_ai = next(
                (
                    r.get("metadata", {}).get("pending_external_ai")
                    for r in chain_results
                    if r.get("metadata", {}).get("need_user_intervention")
                    and r.get("metadata", {}).get("pending_external_ai")
                ),
                None,
            )
            if pending_external_ai:
                s = self.step_state_manager.get(task_id)
                s.current_step_index = current_step_index
                s.goal_contract = goal_contract
                s.authorization_contract = authorization_contract
                s.plan_steps = steps
                s.next_actions.append(
                    {
                        "type": "pending_external_ai",
                        "provider": pending_external_ai.get("provider"),
                        "failure_reason": pending_external_ai.get("failure_reason"),
                    }
                )
                self.step_state_store.save(s)
                self.task_artifact_store.update_state(
                    task_id,
                    status="needs_user",
                    failure_reason=pending_external_ai.get("failure_reason", ""),
                    product_error=product_error(
                        "EXTERNAL_AI_NEED_LOGIN",
                        detail=pending_external_ai.get("failure_reason", ""),
                    ),
                    pending_external_ai=True,
                )
                yield AgentEvent(
                    "external_ai_need_user",
                    {
                        "task_id": task_id,
                        "provider": pending_external_ai.get("provider"),
                        "reason": pending_external_ai.get("failure_reason"),
                        "suggested_user_action": pending_external_ai.get("suggested_user_action"),
                    },
                )
                yield AgentEvent(
                    "external_ai_pending_saved",
                    {"task_id": task_id, "pending": pending_external_ai},
                )
                yield AgentEvent(
                    "stopped",
                    {
                        "task_id": task_id,
                        "reason": "external_ai_need_user",
                        "resume_payload": {"task_id": task_id, "resume_from_task_id": task_id},
                    },
                )
                return
            for r in chain_results:
                if authorization_contract.get(
                    "authorization_mode"
                ) == "full_autonomy" and r.get("metadata", {}).get(
                    "autonomous_actions"
                ):
                    ev = self.evidence_board.save(
                        task_id,
                        step_id,
                        "autonomous_action",
                        "skill_router",
                        json.dumps(
                            r.get("metadata", {}).get("autonomous_actions"),
                            ensure_ascii=False,
                        ),
                        "Full autonomy action executed within granted capabilities",
                    )
                    all_evidence.append(ev)
                evidence_entries = self.evidence_board.save_from_result(
                    task_id, step_id, r
                )
                summarized = self.tool_summarizer.summarize(
                    r.get("skill", "unknown"), r
                )
                if step.get("tool_context", {}).get("continue_on_failure"):
                    summarized.setdefault("metadata", {})["expected_failure"] = True
                r["summary"] = summarized
                all_evidence.extend(evidence_entries)
                all_results.append(summarized)
            step_success = any(r.get("success") for r in chain_results)
            yield AgentEvent(
                "step_result",
                {
                    "step": current_step_index + 1,
                    "success": step_success,
                    "results": chain_results,
                },
            )
            self.task_artifact_store.append_step_log(
                task_id,
                {
                    "type": "step_result",
                    "step": current_step_index + 1,
                    "success": step_success,
                    "results": chain_results,
                },
            )
            if step_success:
                consecutive_failures = 0
                self.step_state_manager.mark_completed(
                    task_id, step, {"results": chain_results}
                )
                self.step_state_store.save(self.step_state_manager.get(task_id))
                current_step_index += 1
            else:
                consecutive_failures += 1
                self.step_state_manager.mark_failed(
                    task_id,
                    step,
                    next(
                        (r.get("error") for r in chain_results if r.get("error")),
                        "Unknown",
                    ),
                )
                self.step_state_store.save(self.step_state_manager.get(task_id))
                failure_info = {
                    "step": step,
                    "results": chain_results,
                    "goal_contract": goal_contract,
                    "authorization_contract": authorization_contract,
                    "error": next(
                        (r.get("error") for r in chain_results if r.get("error")),
                        "Unknown",
                    ),
                }
                repair = (
                    self._structured_failure_repair(failure_info)
                    if structured_plan
                    else await self.failure_handler.diagnose(failure_info, state)
                )
                if step.get("tool_context", {}).get("continue_on_failure"):
                    yield AgentEvent("failure_repair", {"repair": repair})
                    self.step_state_manager.mark_completed(
                        task_id,
                        step,
                        {"results": chain_results, "expected_failure": True},
                    )
                    self.step_state_store.save(self.step_state_manager.get(task_id))
                    consecutive_failures = 0
                    current_step_index += 1
                    continue
                if structured_plan:
                    yield AgentEvent("failure_repair", {"repair": repair})
                    current_step_index += 1
                    continue
                step_state_now = self.step_state_manager.get(task_id)
                if self.escalation_router.should_escalate(
                    repair.get("failure_type", ""),
                    {"retry_count": step_state_now.retry_count},
                ):
                    target = self.escalation_router.choose_target(
                        repair.get("failure_type", ""),
                        authorization_contract.get("available_external_ai", []),
                    )
                    repair["escalation"] = {
                        "needed": True,
                        "target": target,
                        "reason": repair.get("failure_type"),
                    }
                    escalation_prompt = self._build_escalation_prompt(
                        goal_contract,
                        authorization_contract,
                        step,
                        failure_info,
                        relevant_evidence,
                    )
                    escalation_skill = (
                        "web_ai"
                        if "operate_browser"
                        in authorization_contract.get("granted_capabilities", [])
                        else "external_ai"
                    )
                    escalation_result = await self.skill_router.execute_chain(
                        [escalation_skill],
                        escalation_prompt,
                        {
                            "task_id": task_id,
                            "step": step,
                            "goal_contract": goal_contract,
                            "authorization_contract": authorization_contract,
                            "target": target,
                            "provider": (target or "").lower(),
                            "reason": repair.get("failure_type"),
                        },
                    )
                    for er in escalation_result:
                        evidence_entries = self.evidence_board.save_from_result(
                            task_id, step_id, er
                        )
                        all_evidence.extend(evidence_entries)
                        all_results.append(
                            self.tool_summarizer.summarize(
                                er.get("skill", escalation_skill), er
                            )
                        )
                    repair["external_ai_result"] = escalation_result
                repair_steps = self.planner.convert_repair_actions_to_steps(
                    repair.get("repair_actions")
                    or repair.get("repair_plan", {}).get("repair_actions", [])
                )
                if repair_steps:
                    steps[current_step_index + 1 : current_step_index + 1] = (
                        repair_steps
                    )
                    yield AgentEvent("plan_updated", {"inserted_steps": repair_steps})
                yield AgentEvent("failure_repair", {"repair": repair})
                if not (
                    authorization_contract.get("execution_policy", {}).get(
                        "autonomous_retry"
                    )
                    and repair.get("should_retry")
                ):
                    current_step_index += 1
            decision = self.supervisor.decide(
                {
                    "loop_count": loop_count,
                    "consecutive_failures": consecutive_failures,
                    "verified": False,
                    "pending_steps": len(steps) - current_step_index,
                    "has_high_risk_action": step.get("risk_level")
                    in ("high", "critical")
                    and authorization_contract.get("authorization_mode")
                    != "full_autonomy",
                }
            )
            if decision in ("stop", "need_user"):
                yield AgentEvent(
                    decision, {"reason": "Supervisor decision based on contracts"}
                )
                break

        verification = (
            self.verifier._heuristic_verify(
                goal_contract.get("success_criteria", []),
                self.verifier._map_evidence(
                    goal_contract.get("success_criteria", []), all_evidence
                ),
                all_results,
            )
            if structured_plan
            else await self.verifier.check_with_contracts(
                goal_contract, authorization_contract, all_results, all_evidence
            )
        )
        yield AgentEvent("verification", {"result": verification})
        report_steps = [{"index": i, **r} for i, r in enumerate(all_results)]
        report = (
            self.reporter._fallback_contract_report(
                goal_contract,
                authorization_contract,
                report_steps,
                all_evidence,
            )
            if structured_plan
            else await self.reporter.generate_with_contracts(
                goal_contract,
                authorization_contract,
                steps=report_steps,
                evidence=all_evidence,
            )
        )
        report_path = self.task_artifact_store.save_report(task_id, report)
        final_status = (
            "success" if verification.get("verified", False) else "completed_unverified"
        )
        self.task_artifact_store.update_state(
            task_id,
            status=final_status,
            verified=verification.get("verified", False),
            evidence_count=len(all_evidence),
            report_path=str(report_path),
            failure_reason=""
            if verification.get("verified", False)
            else verification.get("reason", "verification_failed"),
            product_error=product_error("TASK_SUCCESS")
            if verification.get("verified", False)
            else {},
        )
        yield AgentEvent("report", {"report": report})
        yield AgentEvent(
            "complete",
            {
                "task_id": task_id,
                "verified": verification.get("verified", False),
                "status": final_status,
                "total_steps": len(all_results),
                "evidence_count": len(all_evidence),
                "report_path": str(report_path),
                "success_rate": sum(1 for r in all_results if r.get("success"))
                / max(len(all_results), 1),
            },
        )

    async def resume_with_contracts(
        self, goal_contract: dict, authorization_contract: dict, step_state
    ) -> AsyncGenerator[AgentEvent, None]:
        """Resume a contract task from persisted StepState.current_step_index."""
        task_id = step_state.task_id
        steps = step_state.plan_steps or []
        if not steps:
            yield AgentEvent("error", {"message": "Checkpoint has no plan_steps"})
            return
        yield AgentEvent(
            "resumed",
            {"task_id": task_id, "current_step_index": step_state.current_step_index},
        )
        all_results = list(step_state.last_tool_results or [])
        all_evidence = self.evidence_board.get_task_evidence(task_id)
        current_step_index = step_state.current_step_index
        consecutive_failures = 0
        while current_step_index < len(steps):
            step = steps[current_step_index]
            step_id = f"step_{current_step_index + 1}"
            yield AgentEvent(
                "step_start",
                {
                    "task_id": task_id,
                    "step": current_step_index + 1,
                    "total": len(steps),
                    "goal": step.get("goal", ""),
                    "resumed": True,
                },
            )
            state = self.observer.collect(
                task_id=task_id,
                recent_results=all_results[-3:],
                evidence_summary=self.evidence_board.get_summary(task_id),
            )
            state["goal_contract"] = goal_contract
            state["authorization_contract"] = authorization_contract
            gap = await self.gap_detector.detect(step, state)
            skill_chain = self.skill_router.select(step, gap, authorization_contract)
            yield AgentEvent("skills_selected", {"chain": skill_chain})
            instruction = await self._generate_instruction(
                {"main_goal": goal_contract.get("final_goal", "")}, step, gap
            )
            context = {
                "task_id": task_id,
                "step_index": current_step_index,
                "step": step,
                "goal_contract": goal_contract,
                "authorization_contract": authorization_contract,
                "gap": gap,
                "previous_results": all_results[-3:],
            }
            context.update(
                self._materialize_tool_context(
                    step, authorization_contract, all_results
                )
            )
            chain_results = await self.skill_router.execute_chain(
                skill_chain, instruction, context
            )
            pending_external_ai = next(
                (
                    r.get("metadata", {}).get("pending_external_ai")
                    for r in chain_results
                    if r.get("metadata", {}).get("need_user_intervention")
                    and r.get("metadata", {}).get("pending_external_ai")
                ),
                None,
            )
            if pending_external_ai:
                s = self.step_state_manager.get(task_id)
                s.current_step_index = current_step_index
                s.goal_contract = goal_contract
                s.authorization_contract = authorization_contract
                s.plan_steps = steps
                s.next_actions.append(
                    {
                        "type": "pending_external_ai",
                        "provider": pending_external_ai.get("provider"),
                        "failure_reason": pending_external_ai.get("failure_reason"),
                    }
                )
                self.step_state_store.save(s)
                yield AgentEvent(
                    "external_ai_need_user",
                    {
                        "task_id": task_id,
                        "provider": pending_external_ai.get("provider"),
                        "reason": pending_external_ai.get("failure_reason"),
                        "suggested_user_action": pending_external_ai.get("suggested_user_action"),
                    },
                )
                yield AgentEvent(
                    "external_ai_pending_saved",
                    {"task_id": task_id, "pending": pending_external_ai},
                )
                yield AgentEvent(
                    "stopped",
                    {
                        "task_id": task_id,
                        "reason": "external_ai_need_user",
                        "resume_payload": {"task_id": task_id, "resume_from_task_id": task_id},
                    },
                )
                return
            for r in chain_results:
                evidence_entries = self.evidence_board.save_from_result(
                    task_id, step_id, r
                )
                all_evidence.extend(evidence_entries)
                all_results.append(
                    self.tool_summarizer.summarize(r.get("skill", "unknown"), r)
                )
            step_success = any(r.get("success") for r in chain_results)
            yield AgentEvent(
                "step_result",
                {
                    "step": current_step_index + 1,
                    "success": step_success,
                    "results": chain_results,
                },
            )
            if step_success:
                self.step_state_manager.mark_completed(
                    task_id, step, {"results": chain_results}
                )
                current_step_index += 1
            else:
                consecutive_failures += 1
                self.step_state_manager.mark_failed(
                    task_id,
                    step,
                    next(
                        (r.get("error") for r in chain_results if r.get("error")),
                        "Unknown",
                    ),
                )
                if consecutive_failures >= 2:
                    break
            s = self.step_state_manager.get(task_id)
            s.goal_contract = goal_contract
            s.authorization_contract = authorization_contract
            s.plan_steps = steps
            s.current_step_index = current_step_index
            s.resumed_from_checkpoint = True
            self.step_state_store.save(s)
        verification = await self.verifier.check_with_contracts(
            goal_contract, authorization_contract, all_results, all_evidence
        )
        yield AgentEvent("verification", {"result": verification})
        report = await self.reporter.generate_with_contracts(
            goal_contract,
            authorization_contract,
            steps=[
                {"index": i, **r}
                for i, r in enumerate(all_results)
                if isinstance(r, dict)
            ],
            evidence=all_evidence,
            resumed_from_checkpoint=True,
        )
        yield AgentEvent("report", {"report": report})
        yield AgentEvent(
            "complete",
            {
                "task_id": task_id,
                "verified": verification.get("verified", False),
                "status": "success"
                if verification.get("verified", False)
                else "completed_unverified",
                "resumed": True,
            },
        )

    async def resume_from_step_state(
        self, task_id: str
    ) -> AsyncGenerator[AgentEvent, None]:
        state = self.step_state_store.load(task_id)
        if not state:
            yield AgentEvent("error", {"message": f"No resumable task: {task_id}"})
            return
        state.resumed_from_checkpoint = True
        self.step_state_manager.states[task_id] = state
        async for event in self.resume_with_contracts(
            state.goal_contract, state.authorization_contract, state
        ):
            yield event

    def _build_escalation_prompt(
        self,
        goal_contract: dict,
        authorization_contract: dict,
        step: dict,
        failure_info: dict,
        evidence: list[dict],
    ) -> str:
        return f"""你是外部专家 AI。请帮助 local-ai-orchestrator 修复当前失败。
Goal Contract: {json.dumps(goal_contract, ensure_ascii=False)}
Authorization Contract: {json.dumps(authorization_contract, ensure_ascii=False)}
当前步骤: {json.dumps(step, ensure_ascii=False)}
失败信息: {json.dumps(failure_info, ensure_ascii=False)}
相关证据: {json.dumps(evidence[:5], ensure_ascii=False)}
请给出具体、可执行的修复步骤，不要泛泛而谈。"""

    async def _generate_instruction(self, goal: dict, step: dict, gap: dict) -> str:
        """Generate a specific instruction for skill execution."""
        if step.get("structured_action"):
            return step.get("goal", "Execute structured local action")
        messages = [
            LLMMessage(
                role="system",
                content="""根据任务目标和当前步骤，生成一条具体的执行指令。
指令要明确、可执行，包含必要的上下文信息。直接输出指令文本，不要包装。""",
            ),
            LLMMessage(
                role="user",
                content=f"""目标: {goal.get('main_goal', '')}
当前步骤: {step.get('goal', '')}
能力缺口: {gap.get('gap_type', 'none')}
需要的技能: {step.get('needed_skills', [])}""",
            ),
        ]
        try:
            resp = await self.llm.chat(messages, temperature=0.3, max_tokens=500)
            return resp.content
        except Exception:
            return step.get("goal", "Execute task")

    def _structured_failure_repair(self, failure_info: dict) -> dict:
        """Diagnose deterministic task failures without depending on the LLM."""
        error = str(failure_info.get("error") or "Unknown")
        plan = self.failure_handler.repair_planner.plan(
            error,
            failure_info.get("goal_contract") or {},
            failure_info.get("authorization_contract") or {},
        )
        return {
            "failure_type": plan.get("failure_type", "tool_failure"),
            "symptom": error,
            "possible_causes": ["Rule planner diagnosis"],
            "repair_actions": plan.get("repair_actions", []),
            "repair_plan": plan,
            "can_auto_repair": plan.get("should_retry", False),
            "should_retry": plan.get("should_retry", True),
            "fallback_used": True,
            "local_model_status": "FALLBACK_USED",
        }

    def _materialize_tool_context(
        self,
        step: dict,
        authorization_contract: dict,
        previous_results: list[dict],
    ) -> dict:
        """Resolve structured step parameters into concrete skill context."""
        tool_context = dict(step.get("tool_context") or {})
        resources = authorization_contract.get("provided_resources") or {}
        project_path = str(resources.get("project_path") or "").strip()
        if project_path:
            tool_context.setdefault("cwd", project_path)
            path = str(tool_context.get("path") or "").strip()
            if path and not os.path.isabs(path):
                tool_context["path"] = os.path.join(project_path, path)

        if tool_context.pop("content_from_previous_stdout", False):
            stdout = ""
            for result in reversed(previous_results):
                metadata = result.get("metadata") or {}
                stdout = str(metadata.get("stdout") or "").strip()
                if stdout:
                    break
            tool_context["content"] = (
                str(tool_context.pop("content_prefix", ""))
                + stdout
                + str(tool_context.pop("content_suffix", ""))
            )
        if tool_context.pop("content_from_previous_result", False):
            result_text = ""
            for result in reversed(previous_results):
                result_text = str(
                    result.get("result") or result.get("summary") or ""
                ).strip()
                if result_text:
                    break
            tool_context["content"] = (
                str(tool_context.pop("content_prefix", ""))
                + result_text
                + str(tool_context.pop("content_suffix", ""))
            )
        return tool_context
