"""Pending action executor for confirmation queue.

Implements in-place continuation for Standard Authorization.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from backend.confirmation.queue import confirmation_queue
from backend.core.agent import Agent
from backend.evidence.board import EvidenceBoard
from backend.local_model.step_state_store import StepStateStore


class PendingActionExecutor:
    def __init__(self):
        self.agent = Agent()
        self.evidence_board = EvidenceBoard()
        self.step_state_store = StepStateStore()
        self.failure_handler = self.agent.failure_handler
        self.planner = self.agent.planner

    async def approve_and_execute(self, req_id: str) -> dict:
        req = confirmation_queue.decide(req_id, True)
        # Execute exactly the stored skill chain for this step.
        chain = req.context.get("skill_chain") or ([req.skill] if req.skill else [])
        if not chain:
            return {"error": "No skill_chain stored", "confirmation": asdict(req)}

        task_id = req.task_id
        step_id = req.step_id
        goal_contract = req.context.get("goal_contract") or {}
        authorization_contract = req.context.get("authorization_contract") or {}

        results = await self.agent.skill_router.execute_chain(
            chain,
            req.instruction or "",
            {
                "task_id": task_id,
                "step": req.context.get("step") or {},
                "goal_contract": goal_contract,
                "authorization_contract": authorization_contract,
                "command": req.payload.get("instruction"),
            },
        )

        # Persist evidence and advance step state.
        if task_id and step_id:
            for r in results:
                self.evidence_board.save_from_result(task_id, step_id, r)
            # Mark the step completed in persisted state
            state = self.step_state_store.load(task_id)
            if state:
                # Move index forward if this approval corresponds to current step
                if req.context.get(
                    "step_index"
                ) is not None and state.current_step_index == req.context.get(
                    "step_index"
                ):
                    state.completed_steps.append(
                        {"step": req.context.get("step"), "result": results}
                    )
                    state.current_step_index += 1
                state.last_tool_results.append(
                    {"confirmation_id": req_id, "results": results}
                )
                state.next_actions = []
                self.step_state_store.save(state)

        self.evidence_board.save(
            task_id,
            step_id,
            "user_decision",
            "confirmation_queue",
            json.dumps({"id": req_id, "decision": "approved"}, ensure_ascii=False),
            "User approved pending action",
        )

        return {
            "confirmation": asdict(req),
            "executed": True,
            "results": results,
            "task_id": task_id,
        }

    async def reject_and_repair(self, req_id: str, reason: str | None = None) -> dict:
        req = confirmation_queue.decide(req_id, False)
        task_id = req.task_id
        step_id = req.step_id

        self.evidence_board.save(
            task_id,
            step_id,
            "user_decision",
            "confirmation_queue",
            json.dumps(
                {"id": req_id, "decision": "rejected", "reason": reason or ""},
                ensure_ascii=False,
            ),
            "User rejected pending action",
        )

        state = self.step_state_store.load(task_id) if task_id else None
        goal_contract = (
            (state.goal_contract if state else None)
            or req.context.get("goal_contract")
            or {}
        )
        authorization_contract = (
            (state.authorization_contract if state else None)
            or req.context.get("authorization_contract")
            or {}
        )

        failure_info = {
            "error": f"User rejected pending action {req.action}. Reason: {reason or ''}",
            "step": req.context.get("step") or {},
            "goal_contract": goal_contract,
            "authorization_contract": authorization_contract,
            "results": [],
        }

        diagnosis = await self.failure_handler.diagnose(
            failure_info,
            {
                "goal_contract": goal_contract,
                "authorization_contract": authorization_contract,
                "optimized_context": {
                    "goal_contract": goal_contract,
                    "authorization_contract": authorization_contract,
                    "current_step": req.context.get("step") or {},
                    "state_summary": "rejected pending action",
                    "relevant_evidence": [],
                    "available_skills": [],
                },
            },
        )

        repair_steps = self.planner.convert_repair_actions_to_steps(
            diagnosis.get("repair_actions")
            or diagnosis.get("repair_plan", {}).get("repair_actions", [])
        )

        if state and repair_steps:
            idx = state.current_step_index
            state.plan_steps[idx:idx] = repair_steps
            state.next_actions = [
                {"type": "repair_inserted", "count": len(repair_steps)}
            ]
            self.step_state_store.save(state)

        return {
            "confirmation": asdict(req),
            "executed": False,
            "repair_steps_inserted": repair_steps,
            "diagnosis": diagnosis,
            "task_id": task_id,
        }
