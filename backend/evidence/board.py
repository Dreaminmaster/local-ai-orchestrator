"""Project-local evidence board used by agent runs and E2E tests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class EvidenceBoard:
    def __init__(self, root: str = "runtime/evidence"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _task_path(self, task_id: str) -> Path:
        safe_id = task_id or "unknown"
        return self.root / f"{safe_id}.jsonl"

    def save(
        self,
        task_id: str,
        step_id: str | None,
        evidence_type: str,
        source: str,
        content: str,
        summary: str = "",
        metadata: dict | None = None,
    ) -> dict:
        entry = {
            "id": uuid4().hex[:12],
            "task_id": task_id,
            "step_id": step_id,
            "type": evidence_type,
            "source": source,
            "content": content,
            "summary": summary,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        path = self._task_path(task_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def save_from_result(self, task_id: str, step_id: str | None, result: dict) -> list[dict]:
        evidence = []
        for item in result.get("evidence") or []:
            evidence.append(
                self.save(
                    task_id,
                    step_id,
                    "artifact",
                    result.get("skill", "unknown"),
                    str(item),
                    f"Evidence artifact from {result.get('skill', 'unknown')}",
                )
            )
        if result.get("result") or result.get("error"):
            evidence.append(
                self.save(
                    task_id,
                    step_id,
                    "tool_result",
                    result.get("skill", "unknown"),
                    json.dumps(result, ensure_ascii=False, default=str),
                    str(result.get("error") or result.get("result", ""))[:500],
                )
            )
        return evidence

    def get_task_evidence(self, task_id: str) -> list[dict]:
        path = self._task_path(task_id)
        if not path.exists():
            return []
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    def get_summary(self, task_id: str, limit: int = 10) -> str:
        entries = self.get_task_evidence(task_id)[-limit:]
        if not entries:
            return "No evidence recorded yet."
        return "\n".join(
            f"- {e.get('type')} from {e.get('source')}: {e.get('summary') or str(e.get('content', ''))[:120]}"
            for e in entries
        )

