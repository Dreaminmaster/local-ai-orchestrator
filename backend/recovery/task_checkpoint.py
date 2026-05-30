from pathlib import Path
import json
from datetime import datetime
class TaskCheckpoint:
    def __init__(self, root: str = 'runtime/checkpoints'):
        self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def save(self, task_id: str, state: dict) -> str:
        p=self.root/f'{task_id}.json'; state=dict(state); state['checkpointed_at']=datetime.now().isoformat(); p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8'); return str(p)
    def load(self, task_id: str) -> dict | None:
        p=self.root/f'{task_id}.json'; return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
