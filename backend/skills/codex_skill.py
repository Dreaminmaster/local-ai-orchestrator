"""Codex Skill — Adapter for code-focused agents/CLIs.

This skill is intentionally conservative. It can call an installed command such
as `codex`, `claude`, or another code agent CLI when configured, but defaults to
returning an actionable instruction rather than pretending the CLI exists.
"""
from __future__ import annotations
import asyncio
import os
from .base import Skill, SkillResult, RiskLevel


class CodexSkill(Skill):
    name = "codex"
    description = "Delegate code repair or implementation to a configured code-agent CLI"
    capabilities = ["code_fix", "code_review", "code_generation", "debugging"]
    risk_level = RiskLevel.MEDIUM

    async def can_handle(self, task: dict, state: dict) -> bool:
        desc = task.get("description", "").lower()
        return any(k in desc for k in ["code", "bug", "debug", "fix", "implement"])

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        cli = os.getenv("CODE_AGENT_CLI", "").strip()
        cwd = context.get("cwd", os.getcwd())
        if not cli:
            return SkillResult(
                skill=self.name,
                success=True,
                result=(
                    "No CODE_AGENT_CLI configured. Use this instruction with your preferred "
                    f"code agent: {instruction}"
                ),
                needs_follow_up=True,
                suggested_next_action="configure_CODE_AGENT_CLI_or_use_file_skill",
                metadata={"mode": "advisory"},
            )

        cmd = f"{cli} {instruction!r}"
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            out, err = await asyncio.wait_for(proc.communicate(), timeout=300)
            stdout = out.decode("utf-8", errors="replace")
            stderr = err.decode("utf-8", errors="replace")
            return SkillResult(
                skill=self.name,
                success=proc.returncode == 0,
                result=stdout or stderr,
                error=None if proc.returncode == 0 else stderr,
                metadata={"command": cmd, "exit_code": proc.returncode},
            )
        except Exception as exc:
            return SkillResult(skill=self.name, success=False, result="", error=str(exc))
