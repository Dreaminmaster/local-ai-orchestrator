"""Persist resumable external AI actions under runtime/tasks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class PendingExternalAIStore:
    def __init__(self, root: str | Path = "runtime/tasks"):
        self.root = Path(root)

    def path(self, task_id: str) -> Path:
        d = self.root / task_id
        d.mkdir(parents=True, exist_ok=True)
        return d / "pending_external_ai.json"

    def save(
        self,
        *,
        task_id: str,
        step_id: str,
        provider: str,
        original_prompt: str,
        redacted_prompt: str,
        context: dict,
        provider_status: str,
        failure_reason: str,
        suggested_user_action: str,
        can_resume: bool = True,
    ) -> dict:
        payload = {
            "task_id": task_id,
            "step_id": step_id,
            "provider": provider,
            "original_prompt": original_prompt,
            "redacted_prompt": redacted_prompt,
            "context": context,
            "provider_status": provider_status,
            "failure_reason": failure_reason,
            "suggested_user_action": suggested_user_action,
            "can_resume": can_resume,
            "created_at": datetime.now().isoformat(),
        }
        self.path(task_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return payload

    def load(self, task_id: str) -> dict:
        path = self.path(task_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def list_pending(self) -> list[dict]:
        out: list[dict] = []
        for path in sorted(self.root.glob("*/pending_external_ai.json")):
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                pass
        return out

    def clear(self, task_id: str) -> None:
        path = self.path(task_id)
        if path.exists():
            path.unlink()


pending_external_ai_store = PendingExternalAIStore()
