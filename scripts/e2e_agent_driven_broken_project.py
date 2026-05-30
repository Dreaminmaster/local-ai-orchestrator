#!/usr/bin/env python3
"""Agent-driven broken project E2E.

The script does not directly patch files. It asks Agent to run the repair loop and
records the event chain/report. A real local/external model is recommended.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_broken_project_agent.json"


async def main():
    src = ROOT / "tests/fixtures/broken_python_project"
    work = ROOT / "runtime/tmp/agent_broken_python_project"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(src, work)

    goal_contract = {
        "goal_mode": "autonomous",
        "original_input": "修复 broken_python_project，让 python3 main.py 成功运行。",
        "final_goal": "修复 Python 项目运行错误并生成证据报告。",
        "assumptions": [
            "允许修改 runtime/tmp/agent_broken_python_project 下的测试副本"
        ],
        "success_criteria": [
            "shell failed 事件被记录",
            "failure_repair 类型为 code_failed 或 tool_failure",
            "产生 repair step",
            "重新运行成功或报告未完成原因",
            "生成最终报告",
        ],
    }
    authorization_contract = {
        "authorization_mode": "full_autonomy",
        "granted_capabilities": [
            "read_files",
            "write_files",
            "run_shell",
            "modify_code",
            "ask_external_ai",
        ],
        "provided_resources": {"project_path": str(work)},
        "available_external_ai": [],
        "execution_policy": {
            "ask_during_execution": False,
            "autonomous_retry": True,
            "autonomous_repair": True,
        },
        "user_confirmed_authorization": True,
    }

    events = []
    async for ev in Agent().run_with_contracts(goal_contract, authorization_contract):
        events.append(ev.to_dict())
        if ev.type == "complete":
            break

    report = {
        "created_at": datetime.now().isoformat(),
        "fixture": str(work),
        "events": events,
        "event_types": [e["type"] for e in events],
        "notes": "Agent-driven: this script does not directly edit files; modifications must come from Agent skills.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
