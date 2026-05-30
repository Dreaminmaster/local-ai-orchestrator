#!/usr/bin/env python3
"""Verify resume starts from current_step_index and does not repeat step 1."""

import asyncio
from backend.core.agent import Agent
from backend.local_model.step_state import StepState


async def main():
    agent = Agent()
    state = StepState(
        task_id="resume_test",
        current_step_index=1,
        completed_steps=[
            {"step": {"step": 1, "goal": "already done"}, "result": {"ok": True}}
        ],
        goal_contract={
            "final_goal": "resume test",
            "success_criteria": ["step 2 executed"],
        },
        authorization_contract={
            "authorization_mode": "full_autonomy",
            "granted_capabilities": ["read_files"],
        },
        plan_steps=[
            {
                "step": 1,
                "goal": "SHOULD_NOT_REPEAT",
                "needed_skills": ["memory"],
                "risk_level": "low",
            },
            {
                "step": 2,
                "goal": "execute resumed step",
                "needed_skills": ["memory"],
                "risk_level": "low",
            },
        ],
    )
    events = []
    async for ev in agent.resume_with_contracts(
        state.goal_contract, state.authorization_contract, state
    ):
        events.append(ev.to_dict())
        if ev.type == "complete":
            break
    step_starts = [e for e in events if e["type"] == "step_start"]
    assert step_starts, "no resumed step_start emitted"
    assert step_starts[0]["data"]["step"] == 2, step_starts
    assert all("SHOULD_NOT_REPEAT" not in str(e) for e in step_starts), step_starts
    print({"ok": True, "first_resumed_step": step_starts[0]["data"]["step"]})


if __name__ == "__main__":
    asyncio.run(main())
