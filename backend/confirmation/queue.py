from pathlib import Path
import json
from .schemas import ConfirmationRequest


class ConfirmationQueue:
    def __init__(self, root: str = "runtime/confirmations"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.items: dict[str, ConfirmationRequest] = {}
        self._load()

    def _path(self, req_id: str) -> Path:
        return self.root / f"{req_id}.json"

    def _load(self):
        for p in self.root.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self.items[data["id"]] = ConfirmationRequest(**data)
            except Exception:
                pass

    def _save(self, req: ConfirmationRequest):
        self._path(req.id).write_text(
            json.dumps(req.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, req: ConfirmationRequest) -> ConfirmationRequest:
        self.items[req.id] = req
        self._save(req)
        return req

    def list(self):
        return list(self.items.values())

    def pending(self):
        return [x for x in self.items.values() if x.status == "pending"]

    def decide(self, req_id: str, approved: bool):
        req = self.items[req_id]
        req.status = "approved" if approved else "rejected"
        self._save(req)
        return req


confirmation_queue = ConfirmationQueue()
