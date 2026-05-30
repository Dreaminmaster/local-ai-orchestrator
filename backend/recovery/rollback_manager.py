from backend.evidence.snapshot import SnapshotManager


class RollbackManager:
    def __init__(self):
        self.snapshots = SnapshotManager()

    def snapshot(self, path: str, reason: str = "checkpoint"):
        return self.snapshots.create(path, reason).__dict__

    def rollback(self, snapshot_id: str):
        return self.snapshots.rollback(snapshot_id).__dict__
