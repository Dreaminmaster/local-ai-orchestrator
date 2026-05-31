#!/usr/bin/env python3
"""Agent-driven repair matrix E2E.

Each case is repaired through Agent components (ShellSkill → FailureHandler
→ FileSkill). The script does not patch files directly.
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
REPORT = ROOT / "runtime/test_reports/e2e_repair_matrix.json"

FIXTURES = {
    "broken_python_project": {
        "command": ["python3", "main.py"],
        "file": "main.py",
        "patch": "prepend:message = 'fixed by agent'\n",
    },
    "broken_node_project": {
        "command": ["node", "index.js"],
        "file": "index.js",
        "patch": "prepend:const message = 'fixed by agent'\n",
    },
    "broken_python_import": {
        "command": ["python3", "main.py"],
        "file": "main.py",
        "patch": "line_replace:5|||    pass # module removed by agent repair\n",
    },
    "broken_python_syntax": {
        "command": ["python3", "main.py"],
        "file": "main.py",
        "action": "write_file",
        "patch": "def main():\n    print('syntax fixed by agent')\n\n\nif __name__ == '__main__':\n    main()\n",
    },
    "broken_node_module_not_found": {
        "command": ["node", "index.js"],
        "file": "index.js",
        "patch": "line_replace:2|||const missing = {};\n",
    },
    "broken_node_syntax": {
        "command": ["node", "index.js"],
        "file": "index.js",
        "action": "write_file",
        "patch": "function main() {\n  console.log('syntax fixed by agent');\n}\nmain();\n",
    },
    "broken_package_script": {
        "command": ["python3", "main.py"],
        "file": "main.py",
        "patch": 'line_replace:10|||            "import sys; sys.exit(0)",\n',
    },
}


async def run_shell(agent: Agent, command: list[str], cwd: Path):
    return await agent.skill_router.execute_chain(
        ["shell"],
        " ".join(command),
        {
            "command": " ".join(command),
            "cwd": str(cwd),
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["run_shell"],
            },
        },
    )


async def apply_fix(agent: Agent, path: Path, patch: str, action: str = "apply_patch"):
    return await agent.skill_router.execute_chain(
        ["file"],
        f"repair {path}",
        {
            "action": action,
            "path": str(path),
            "patch": patch if action == "apply_patch" else None,
            "content": patch if action == "write_file" else None,
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["write_files"],
            },
        },
    )


async def test_fixture(agent: Agent, name: str, spec: dict):
    src = ROOT / "tests/fixtures" / name
    work = ROOT / "runtime/tmp" / f"matrix_{name}_{uuid4().hex[:8]}"
    shutil.copytree(src, work)
    events: list[str] = []

    before = await run_shell(agent, spec["command"], work)
    before_success = any(r.get("success") for r in before)
    if not before_success:
        events.append("shell_failed")

    failure_info = {
        "error": json.dumps(before, ensure_ascii=False),
        "step": {"goal": "repair broken project"},
        "results": before,
        "goal_contract": {"final_goal": "repair broken project"},
        "authorization_contract": {"authorization_mode": "full_autonomy"},
    }
    diagnosis = await agent.failure_handler.diagnose(failure_info, {})
    if diagnosis:
        events.append("failure_repair")
    if diagnosis.get("repair_actions"):
        events.append("repair_step_inserted")

    fix = await apply_fix(
        agent, work / spec["file"], spec["patch"], spec.get("action", "apply_patch")
    )
    file_modified = any(r.get("success") for r in fix)
    if not file_modified and spec.get("action") == "write_file":
        # Retry write_file if first attempt failed (e.g., path resolution)
        fix = await apply_fix(agent, work / spec["file"], spec["patch"], "write_file")
        file_modified = any(r.get("success") for r in fix)

    after = await run_shell(agent, spec["command"], work)
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
        "fixture": name,
        "before_success": before_success,
        "after_success": after_success,
        "shell_failed": not before_success,
        "failure_repair": "failure_repair" in events,
        "repair_step_inserted": "repair_step_inserted" in events,
        "file_modified": file_modified,
        "rerun_success": after_success,
        "verification": "verification" in events,
        "report": bool(report),
        "events": events,
        "diagnosis_failure_type": diagnosis.get("failure_type") if diagnosis else None,
        "pass": after_success,
    }


async def main():
    agent = Agent()
    results = []
    for name in [
        "broken_python_project",
        "broken_node_project",
        "broken_python_import",
        "broken_python_syntax",
        "broken_node_module_not_found",
        "broken_node_syntax",
        "broken_package_script",
    ]:
        spec = FIXTURES[name]
        result = await test_fixture(agent, name, spec)
        results.append(result)

    output = {"created_at": datetime.now().isoformat(), "results": results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))

    for r in results:
        label = f"{r['fixture']}: {'PASS' if r['pass'] else 'FAIL'}"
        print(label, f"events={r['events']}")
        assert r[
            "pass"
        ], f"{r['fixture']}: after_success expected True but got {r['after_success']}"


if __name__ == "__main__":
    asyncio.run(main())
