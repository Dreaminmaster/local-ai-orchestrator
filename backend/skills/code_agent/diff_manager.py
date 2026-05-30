import subprocess
class DiffManager:
    def diff(self, cwd: str = ".") -> str:
        return subprocess.run(["git","diff"], cwd=cwd, text=True, capture_output=True).stdout
    def status(self, cwd: str = ".") -> str:
        return subprocess.run(["git","status","--short"], cwd=cwd, text=True, capture_output=True).stdout
