"""Supervisor — Decide whether to continue, stop, or ask user."""

from __future__ import annotations
import os


class Supervisor:
    """Controls the agent loop: continue, finish, or ask user."""

    def __init__(self):
        self.max_loops = int(os.getenv("MAX_AUTO_LOOPS", "20"))
        self.max_failures = int(os.getenv("MAX_CONSECUTIVE_FAILURES", "5"))

    def decide(self, task_state: dict) -> str:
        """
        Returns one of:
        - "continue": keep executing
        - "finish": task is done
        - "need_user": need user confirmation
        - "stop": too many failures, stop
        """
        loop_count = task_state.get("loop_count", 0)
        consecutive_failures = task_state.get("consecutive_failures", 0)
        verified = task_state.get("verified", False)
        pending_steps = task_state.get("pending_steps", 0)
        has_high_risk = task_state.get("has_high_risk_action", False)

        # Task verified as complete
        if verified:
            return "finish"

        # Too many loops
        if loop_count >= self.max_loops:
            return "stop"

        # Too many consecutive failures
        if consecutive_failures >= self.max_failures:
            return "stop"

        # High risk action needs confirmation
        if has_high_risk:
            return "need_user"

        # No more steps to execute
        if pending_steps <= 0 and loop_count > 0:
            return "finish"

        return "continue"
