class AskOrAssume:
    """Decide whether to ask clarification questions or make explicit assumptions."""
    def decide(self, goal_mode: str, missing: list[str]) -> dict:
        if goal_mode == "clarify_first" and missing:
            return {"action": "ask", "questions": [f"请确认：{m}" for m in missing]}
        return {"action": "assume", "assumptions": [f"默认假设：{m}" for m in missing]}
