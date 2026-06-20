#!/usr/bin/env python3
"""Real-user-shaped local project smoke with no live provider calls."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.agent import Agent
from backend.core.task_artifact_store import TaskArtifactStore

WORKSPACE = Path("/Users/johnwick/Documents/codex/local-ai-orchestrator-real-task-smoke")
REPORT = ROOT / "runtime/test_reports/e2e_real_user_task_smoke.json"


def goal() -> dict:
    task = "检查这个小项目，运行测试，修复明显错误，最后写一份中文修复报告。"
    return {
        "goal_mode": "autonomous",
        "original_input": task,
        "final_goal": task,
        "assumptions": [],
        "user_constraints": ["只操作测试目录", "不调用外部 AI"],
        "success_criteria": ["完成用户目标", "有证据证明结果", "输出最终报告"],
        "user_confirmed_goal": True,
        "completion_standard": "修复后运行成功并生成中文报告",
    }


def authorization() -> dict:
    return {
        "authorization_mode": "full_autonomy",
        "granted_capabilities": [
            "read_files",
            "write_files",
            "run_shell",
            "autonomous_retry",
            "autonomous_repair",
        ],
        "provided_resources": {"project_path": str(WORKSPACE)},
        "available_external_ai": [],
        "execution_policy": {
            "ask_during_execution": False,
            "autonomous_retry": True,
            "autonomous_repair": True,
            "autonomous_external_ai_query": False,
        },
        "user_confirmed_authorization": True,
        "denied_capabilities": ["ask_external_ai", "operate_browser"],
        "protected_paths": [],
    }


async def main() -> int:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "main.py").write_text("print(message)\n", encoding="utf-8")
    (WORKSPACE / "README.md").write_text("# Small smoke project\n", encoding="utf-8")
    (WORKSPACE / "package.json").write_text(
        json.dumps({"name": "local-ai-real-task-smoke", "private": True}, indent=2),
        encoding="utf-8",
    )
    events = []
    async for event in Agent().run_with_contracts(goal(), authorization()):
        events.append(event.to_dict())
    complete = next((e["data"] for e in reversed(events) if e["type"] == "complete"), {})
    stopped = next((e["data"] for e in reversed(events) if e["type"] == "stopped"), {})
    task_id = complete.get("task_id") or stopped.get("task_id") or ""
    state = TaskArtifactStore().get(task_id) if task_id else {}
    final_report = WORKSPACE / "final_report.md"
    output = {
        "created_at": datetime.now().isoformat(),
        "workspace": str(WORKSPACE),
        "task_id": task_id,
        "final_status": complete.get("status") or stopped.get("status") or "FAIL",
        "main_py_fixed": "message =" in (WORKSPACE / "main.py").read_text(encoding="utf-8"),
        "final_report_exists": final_report.exists(),
        "final_report_path": str(final_report),
        "report_path": (state or {}).get("report_path", ""),
        "evidence_count": (state or {}).get("evidence_count", 0),
        "external_ai_live_called": False,
        "event_types": [event["type"] for event in events],
    }
    output["pass"] = bool(
        output["final_status"] == "success"
        and output["main_py_fixed"]
        and output["final_report_exists"]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
