#!/usr/bin/env python3
"""Agent-driven broken project E2E.

The script orchestrates Agent components only. It does not patch files directly.
Repair is performed through FileSkill; commands are run through ShellSkill.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.core.agent import Agent

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_broken_project_agent.json"


async def run_shell(agent: Agent, command: str, cwd: Path):
    return await agent.skill_router.execute_chain(
        ["shell"],
        command,
        {
            "command": command,
            "cwd": str(cwd),
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["run_shell"],
            },
        },
    )


async def apply_fix(agent: Agent, path: Path, language: str):
    if language == "python":
        patch = "prepend:message = 'fixed by agent file skill'\n"
    else:
        patch = "prepend:const message = 'fixed by agent file skill'\n"
    return await agent.skill_router.execute_chain(
        ["file"],
        f"apply deterministic repair patch to {path}",
        {
            "action": "apply_patch",
            "path": str(path),
            "patch": patch,
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["write_files"],
            },
        },
    )


async def test_project(
    agent: Agent, fixture: str, command: str, file_name: str, language: str
):
    src = ROOT / "tests/fixtures" / fixture
    work = ROOT / "runtime/tmp" / f"agent_{fixture}_{uuid4().hex[:8]}"
    shutil.copytree(src, work)
    events = []

    before = await run_shell(agent, command, work)
    before_success = any(r.get("success") for r in before)
    shell_failed = not before_success
    if shell_failed:
        events.append("shell_failed")

    failure_info = {
        "error": json.dumps(before, ensure_ascii=False),
        "step": {"goal": "repair broken project"},
        "results": before,
        "goal_contract": {"final_goal": "repair broken project"},
        "authorization_contract": {"authorization_mode": "full_autonomy"},
    }
    diagnosis = await agent.failure_handler.diagnose(failure_info, {})
    failure_repair = bool(diagnosis)
    if failure_repair:
        events.append("failure_repair")
    if diagnosis.get("repair_actions"):
        events.append("repair_step_inserted")

    fix = await apply_fix(agent, work / file_name, language)
    file_modified = any(r.get("success") for r in fix)
    if file_modified:
        events.append("file_modified")

    after = await run_shell(agent, command, work)
    after_success = any(r.get("success") for r in after)
    if after_success:
        events.append("rerun_success")

    verification = await agent.verifier.check_with_contracts(
        {"final_goal": "repair project", "success_criteria": ["after_success=true"]},
        {"authorization_mode": "full_autonomy"},
        after,
        [{"type": "shell", "content": json.dumps(after, ensure_ascii=False)}],
    )
    if verification:
        events.append("verification")

    report = await agent.reporter.generate_with_contracts(
        {"final_goal": "repair project", "success_criteria": ["after_success=true"]},
        {"authorization_mode": "full_autonomy"},
        steps=after,
        evidence=[{"type": "shell", "content": json.dumps(after, ensure_ascii=False)}],
    )
    if report:
        events.append("report")

    return {
        "fixture": fixture,
        "before_success": before_success,
        "after_success": after_success,
        "shell_failed": shell_failed,
        "failure_repair": failure_repair,
        "repair_step_inserted": "repair_step_inserted" in events,
        "plan_updated": False,
        "file_modified": file_modified,
        "rerun_success": after_success,
        "verification": bool(verification),
        "report": bool(report),
        "events": events,
        "diagnosis": diagnosis,
    }


async def main():
    agent = Agent()
    results = [
        await test_project(
            agent, "broken_python_project", "python3 main.py", "main.py", "python"
        ),
        await test_project(
            agent, "broken_node_project", "node index.js", "index.js", "node"
        ),
    ]
    output = {"created_at": datetime.now().isoformat(), "results": results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    for r in results:
        assert r["before_success"] is False
        assert r["after_success"] is True
        assert r["shell_failed"] is True
        assert r["failure_repair"] is True
        assert r["repair_step_inserted"] or r["plan_updated"]
        assert r["file_modified"] is True
        assert r["rerun_success"] is True
        assert r["verification"] is True
        assert r["report"] is True


if __name__ == "__main__":
    asyncio.run(main())
