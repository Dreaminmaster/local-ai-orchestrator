"""Observer — Collect state from execution environment and evidence."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EnvironmentState:
    task_id: str | None = None
    cwd: str = "."
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    files: list[str] = field(default_factory=list)
    recent_results: list[dict] = field(default_factory=list)
    evidence_summary: dict = field(default_factory=dict)
    browser_state: dict = field(default_factory=dict)
    desktop_state: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "cwd": self.cwd,
            "timestamp": self.timestamp,
            "files": self.files,
            "recent_results": self.recent_results,
            "evidence_summary": self.evidence_summary,
            "browser_state": self.browser_state,
            "desktop_state": self.desktop_state,
            "notes": self.notes,
        }


class Observer:
    """Collects observable state for planning, verification, and recovery."""

    def collect(
        self,
        task_id: str | None = None,
        cwd: str = ".",
        recent_results: list[dict] | None = None,
        evidence_summary: dict | None = None,
    ) -> dict:
        files = []
        try:
            p = Path(cwd)
            if p.exists() and p.is_dir():
                files = [str(x.name) for x in list(p.iterdir())[:50]]
        except Exception as exc:
            files = [f"observer_error: {exc}"]

        return EnvironmentState(
            task_id=task_id,
            cwd=cwd,
            files=files,
            recent_results=recent_results or [],
            evidence_summary=evidence_summary or {},
        ).to_dict()
