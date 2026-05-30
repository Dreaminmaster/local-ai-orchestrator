from dataclasses import dataclass, field


@dataclass
class StepState:
    task_id: str
    current_step_index: int = 0
    completed_steps: list[dict] = field(default_factory=list)
    failed_steps: list[dict] = field(default_factory=list)
    retry_count: int = 0
    last_tool_results: list[dict] = field(default_factory=list)
    next_actions: list[dict] = field(default_factory=list)
    goal_contract: dict = field(default_factory=dict)
    authorization_contract: dict = field(default_factory=dict)
    plan_steps: list[dict] = field(default_factory=list)
    resumed_from_checkpoint: bool = False


class StepStateManager:
    def __init__(self):
        self.states: dict[str, StepState] = {}

    def get(self, task_id: str) -> StepState:
        if task_id not in self.states:
            self.states[task_id] = StepState(task_id=task_id)
        return self.states[task_id]

    def initialize_contracts(
        self,
        task_id: str,
        goal_contract: dict,
        authorization_contract: dict,
        plan_steps: list[dict],
    ):
        s = self.get(task_id)
        s.goal_contract = goal_contract
        s.authorization_contract = authorization_contract
        s.plan_steps = plan_steps
        return s

    def mark_completed(self, task_id: str, step: dict, result: dict):
        s = self.get(task_id)
        s.completed_steps.append({"step": step, "result": result})
        s.current_step_index += 1
        s.retry_count = 0
        s.last_tool_results.append(result)

    def mark_failed(self, task_id: str, step: dict, error: str):
        s = self.get(task_id)
        s.failed_steps.append({"step": step, "error": error})
        s.retry_count += 1
