"""Simple project-local file snapshots."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class SnapshotResult:
    success: bool
    snapshot_id: str = ""
    path: str = ""
    snapshot_path: str = ""
    error: str = ""
    evidence: list[str] = field(default_factory=list)


class SnapshotManager:
    def __init__(self, root: str = "runtime/evidence/snapshots"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, path: str, reason: str = "checkpoint") -> SnapshotResult:
        src = Path(path)
        if not src.exists() or not src.is_file():
            return SnapshotResult(success=False, path=path, error="File not found for snapshot")
        snapshot_id = uuid4().hex[:12]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst_dir = self.root / snapshot_id
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{src.name}.{stamp}.bak"
        shutil.copy2(src, dst)
        return SnapshotResult(
            success=True,
            snapshot_id=snapshot_id,
            path=str(src),
            snapshot_path=str(dst),
            evidence=[str(dst), reason],
        )

    def rollback(self, snapshot_id: str) -> SnapshotResult:
        snapshot_dir = self.root / snapshot_id
        if not snapshot_dir.exists():
            return SnapshotResult(success=False, snapshot_id=snapshot_id, error="Snapshot not found")
        snapshots = sorted(snapshot_dir.glob("*.bak"))
        if not snapshots:
            return SnapshotResult(success=False, snapshot_id=snapshot_id, error="Snapshot file not found")
        snapshot = snapshots[-1]
        original_name = snapshot.name.rsplit(".", 2)[0]
        target = Path.cwd() / original_name
        shutil.copy2(snapshot, target)
        return SnapshotResult(
            success=True,
            snapshot_id=snapshot_id,
            path=str(target),
            snapshot_path=str(snapshot),
            evidence=[str(snapshot), str(target)],
        )
