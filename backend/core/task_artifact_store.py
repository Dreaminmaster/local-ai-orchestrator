"""Durable task artifacts used by the API, UI, and resume flow."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from backend.runtime_paths import resolve_runtime_paths


class TaskArtifactStore:
    """Persist one self-contained directory for every Agent task."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else resolve_runtime_paths().ensure().tasks_dir
        self.root.mkdir(parents=True, exist_ok=True)
        self._event_lock = threading.Lock()

    def task_dir(self, task_id: str) -> Path:
        path = self.root / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def initialize(
        self,
        task_id: str,
        goal_contract: dict,
        authorization_contract: dict,
    ) -> dict:
        state = {
            "task_id": task_id,
            "status": "created",
            "goal_contract": goal_contract,
            "authorization_contract": authorization_contract,
            "failure_reason": "",
            "evidence_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.write_json(task_id, "task_state.json", state)
        self.write_json(task_id, "plan.json", {"plan": [], "total_steps": 0})
        return state

    def update_state(self, task_id: str, **changes) -> dict:
        state = self.read_json(task_id, "task_state.json") or {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
        }
        state.update(changes)
        state["updated_at"] = datetime.now().isoformat()
        self.write_json(task_id, "task_state.json", state)
        return state

    def save_plan(self, task_id: str, plan: dict) -> None:
        self.write_json(task_id, "plan.json", plan)

    def append_step_log(self, task_id: str, entry: dict) -> None:
        entry = dict(entry)
        entry.setdefault("created_at", datetime.now().isoformat())
        path = self.task_dir(task_id) / "step_logs.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def append_event(
        self,
        task_id: str,
        event_type: str,
        *,
        stage: str = "",
        step_id: str = "",
        status: str = "",
        summary: str = "",
        progress_percent: int = 0,
        retry_count: int = 0,
        tool_name: str = "",
        safe_payload: dict | None = None,
    ) -> dict:
        """Append one bounded, replayable UI event without sensitive payloads."""
        with self._event_lock:
            path = self.task_dir(task_id) / "events.jsonl"
            event_id = self._line_count(path) + 1
            event = {
                "event_id": event_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "stage": stage,
                "step_id": step_id,
                "status": status,
                "summary": self._bounded_text(summary, 600),
                "progress_percent": max(0, min(int(progress_percent or 0), 100)),
                "retry_count": max(0, int(retry_count or 0)),
                "tool_name": tool_name,
                "safe_payload": self._safe_payload(safe_payload or {}),
            }
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
            return event

    def list_events(self, task_id: str, after_event_id: int = 0) -> list[dict]:
        path = self.task_dir(task_id) / "events.jsonl"
        if not path.exists():
            return []
        events = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                if int(event.get("event_id", 0)) > int(after_event_id or 0):
                    events.append(event)
        except (OSError, json.JSONDecodeError):
            return events
        return events

    def save_report(self, task_id: str, report: str) -> Path:
        path = self.task_dir(task_id) / "final_report.md"
        path.write_text(report, encoding="utf-8")
        return path

    def write_json(self, task_id: str, name: str, data: dict) -> Path:
        path = self.task_dir(task_id) / name
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return path

    def read_json(self, task_id: str, name: str) -> dict | None:
        path = self.task_dir(task_id) / name
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def get(self, task_id: str) -> dict | None:
        state = self.read_json(task_id, "task_state.json")
        if not state:
            return None
        state["plan"] = self.read_json(task_id, "plan.json") or {}
        state["report_available"] = (self.task_dir(task_id) / "final_report.md").exists()
        state["pending_external_ai"] = (
            self.read_json(task_id, "pending_external_ai.json") or None
        )
        state["tool_call_count"] = self._step_log_count(task_id)
        state["event_count"] = len(self.list_events(task_id))
        state["task_dir"] = str(self.task_dir(task_id))
        return state

    def get_report(self, task_id: str) -> str | None:
        path = self.task_dir(task_id) / "final_report.md"
        return path.read_text(encoding="utf-8") if path.exists() else None

    def list_tasks(self, limit: int = 50) -> list[dict]:
        tasks = []
        for path in self.root.glob("*/task_state.json"):
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            state["report_available"] = (path.parent / "final_report.md").exists()
            state["pending_external_ai"] = (path.parent / "pending_external_ai.json").exists()
            state["tool_call_count"] = self._step_log_count(path.parent.name)
            state["event_count"] = len(self.list_events(path.parent.name))
            state["task_dir"] = str(path.parent)
            tasks.append(state)
        return sorted(
            tasks,
            key=lambda item: item.get("updated_at") or item.get("created_at") or "",
            reverse=True,
        )[:limit]

    def _step_log_count(self, task_id: str) -> int:
        path = self.task_dir(task_id) / "step_logs.jsonl"
        if not path.exists():
            return 0
        try:
            return sum(
                1
                for line in path.read_text(encoding="utf-8").splitlines()
                if '"type": "step_result"' in line
            )
        except OSError:
            return 0

    @staticmethod
    def _line_count(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)
        except OSError:
            return 0

    @staticmethod
    def _bounded_text(value: object, limit: int) -> str:
        text = str(value or "")
        return text if len(text) <= limit else f"{text[:limit]}... [truncated]"

    @classmethod
    def _safe_payload(cls, payload: dict) -> dict:
        blocked = {"cookie", "cookies", "token", "secret", "password", "profile_data"}
        safe = {}
        for key, value in payload.items():
            if str(key).lower() in blocked:
                continue
            if isinstance(value, dict):
                safe[key] = cls._safe_payload(value)
            elif isinstance(value, list):
                safe[key] = [
                    cls._safe_payload(item) if isinstance(item, dict) else cls._bounded_text(item, 600)
                    for item in value[:20]
                ]
            else:
                safe[key] = cls._bounded_text(value, 1200)
        return safe
