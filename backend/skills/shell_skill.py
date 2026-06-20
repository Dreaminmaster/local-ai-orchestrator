"""Shell Skill — Execute terminal commands."""

from __future__ import annotations
import asyncio
import os
import platform
from .base import Skill, SkillResult, RiskLevel


class ShellSkill(Skill):
    name = "shell"
    description = "Execute shell commands in the terminal"
    capabilities = ["run_command", "check_output", "install_packages", "run_scripts"]
    risk_level = RiskLevel.MEDIUM

    # Commands that require HIGH risk confirmation
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "rm -r /",
        "mkfs",
        "dd if=",
        "chmod 777",
        "curl | sh",
        "wget | sh",
        "> /dev/sd",
    ]

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = [
            "run",
            "execute",
            "terminal",
            "command",
            "install",
            "build",
            "compile",
        ]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        command = context.get("command", instruction)

        # Safety check
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=f"Blocked dangerous command pattern: {pattern}",
                )

        # Working directory
        cwd = context.get("cwd", os.getcwd())
        timeout = context.get("timeout", 60)
        env = os.environ.copy()
        if platform.system() == "Darwin":
            common_paths = [
                "/usr/local/bin",
                "/opt/homebrew/bin",
                "/Library/Frameworks/Python.framework/Versions/Current/bin",
                "/usr/bin",
                "/bin",
                "/usr/sbin",
                "/sbin",
            ]
            existing = env.get("PATH", "").split(":")
            env["PATH"] = ":".join(dict.fromkeys(common_paths + existing))

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()
            success = process.returncode == 0

            # Save log as evidence
            log_content = f"$ {command}\n"
            if stdout_text:
                log_content += f"[stdout]\n{stdout_text}\n"
            if stderr_text:
                log_content += f"[stderr]\n{stderr_text}\n"
            log_content += f"[exit_code] {process.returncode}\n"

            return SkillResult(
                skill=self.name,
                success=success,
                result=stdout_text if success else stderr_text,
                evidence=[f"shell:{command}"],
                error=stderr_text if not success else None,
                metadata={
                    "command": command,
                    "exit_code": process.returncode,
                    "stdout": stdout_text[:2000],
                    "stderr": stderr_text[:2000],
                },
            )

        except asyncio.TimeoutError:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Command timed out after {timeout}s: {command}",
            )
        except Exception as e:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=str(e),
            )
