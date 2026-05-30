from pathlib import Path
import json
from backend.local_model.step_state import StepState


class StepStateStore:
    def __init__(self, root: str = "runtime/tasks"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        d = self.root / task_id
        d.mkdir(parents=True, exist_ok=True)
        return d / "step_state.json"

    def save(self, state: StepState):
        self._path(state.task_id).write_text(
            json.dumps(state.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load(self, task_id: str) -> StepState | None:
        p = self._path(task_id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return StepState(**data)

    def list_resumable_tasks(self) -> list[StepState]:
        out = []
        for p in self.root.glob("*/step_state.json"):
            try:
                out.append(StepState(**json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                pass
        return out
