from pathlib import Path
import shutil
import uuid


class SandboxWorkspaceManager:
    def __init__(self, root: str = "runtime/sandboxes"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, source: str | None = None) -> str:
        dest = self.root / str(uuid.uuid4())[:12]
        dest.mkdir(parents=True)
        if source:
            src = Path(source)
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            elif src.exists():
                shutil.copy2(src, dest / src.name)
        return str(dest)

    def destroy(self, path: str):
        p = Path(path)
        if p.exists() and self.root in p.parents:
            shutil.rmtree(p)
