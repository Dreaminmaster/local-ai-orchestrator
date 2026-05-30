import asyncio, os
class CodexCLIAdapter:
    def __init__(self, command: str | None = None):
        self.command = command or os.getenv("CODE_AGENT_CLI", "codex")
    async def run(self, prompt: str, cwd: str = ".") -> dict:
        proc = await asyncio.create_subprocess_shell(f"{self.command} {prompt!r}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
        out, err = await proc.communicate()
        return {"success": proc.returncode == 0, "stdout": out.decode(errors='replace'), "stderr": err.decode(errors='replace'), "exit_code": proc.returncode}
