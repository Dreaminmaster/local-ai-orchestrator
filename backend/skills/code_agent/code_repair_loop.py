from .project_analyzer import ProjectAnalyzer
from .diff_manager import DiffManager
from .codex_cli_adapter import CodexCLIAdapter


class CodeRepairLoop:
    def __init__(self):
        self.analyzer = ProjectAnalyzer()
        self.diff = DiffManager()
        self.adapter = CodexCLIAdapter()

    async def repair(self, issue: str, cwd: str = ".") -> dict:
        project = self.analyzer.analyze(cwd)
        prompt = f"Fix this issue in project {project}: {issue}. Make minimal safe changes and keep tests passing."
        result = await self.adapter.run(prompt, cwd)
        return {
            "project": project,
            "agent_result": result,
            "diff": self.diff.diff(cwd),
            "status": self.diff.status(cwd),
        }
