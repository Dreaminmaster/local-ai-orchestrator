from pathlib import Path
class ProjectAnalyzer:
    def analyze(self, root: str = ".") -> dict:
        p=Path(root); files=[x.name for x in p.iterdir()] if p.exists() else []
        stack=[]
        if "package.json" in files: stack.append("node")
        if "pyproject.toml" in files or "requirements.txt" in files: stack.append("python")
        if "Cargo.toml" in files: stack.append("rust")
        return {"root": str(p), "files": files[:100], "stack": stack}
