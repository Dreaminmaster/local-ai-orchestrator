#!/usr/bin/env python3
"""Offline 10-case Agent task matrix with no live External AI calls."""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from backend.core.agent import Agent
from backend.core.task_artifact_store import TaskArtifactStore

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "runtime/tmp/agent_task_matrix"
REPORT = ROOT / "runtime/test_reports/e2e_agent_task_matrix.json"


def goal(task: str) -> dict:
    return {
        "goal_mode": "autonomous",
        "original_input": task,
        "final_goal": task,
        "assumptions": [],
        "user_constraints": ["只操作测试目录", "不调用外部 AI"],
        "success_criteria": ["完成用户目标", "有证据证明结果", "输出最终报告"],
        "user_confirmed_goal": True,
        "completion_standard": "满足成功标准并生成最终报告",
    }


def authorization(path: Path) -> dict:
    return {
        "authorization_mode": "full_autonomy",
        "granted_capabilities": [
            "read_files",
            "write_files",
            "run_shell",
            "autonomous_retry",
            "autonomous_repair",
        ],
        "provided_resources": {"project_path": str(path)},
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


def copy_fixture(name: str, target: Path) -> None:
    shutil.copytree(ROOT / "tests/fixtures" / name, target)


async def run_case(spec: dict) -> dict:
    case_dir = WORK_ROOT / spec["case_name"]
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    if spec.get("fixture"):
        shutil.rmtree(case_dir)
        copy_fixture(spec["fixture"], case_dir)
    for name, content in spec.get("files", {}).items():
        path = case_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    before = {
        str(path.relative_to(case_dir)): path.read_text(encoding="utf-8", errors="replace")
        for path in case_dir.rglob("*")
        if path.is_file()
    }
    started = time.monotonic()
    events = []
    agent = Agent()
    async for event in agent.run_with_contracts(goal(spec["task"]), authorization(case_dir)):
        events.append(event.to_dict())
    duration = round(time.monotonic() - started, 3)
    by_type: dict[str, list[dict]] = {}
    for event in events:
        by_type.setdefault(event["type"], []).append(event["data"])
    complete = (by_type.get("complete") or [{}])[-1]
    stopped = (by_type.get("stopped") or [{}])[-1]
    task_id = complete.get("task_id") or stopped.get("task_id") or ""
    state = TaskArtifactStore().get(task_id) if task_id else None
    after = {
        str(path.relative_to(case_dir)): path.read_text(encoding="utf-8", errors="replace")
        for path in case_dir.rglob("*")
        if path.is_file() and ".snapshots" not in path.parts
    }
    changed = sorted(
        name for name, content in after.items() if before.get(name) != content
    )
    final_status = complete.get("status") or stopped.get("status") or "FAIL"
    expected_status = spec.get("expected_status", "success")
    event_types = [event["type"] for event in events]
    passed = final_status == expected_status
    if spec.get("expect_event"):
        passed = passed and spec["expect_event"] in event_types
    if spec.get("expect_files"):
        passed = passed and all((case_dir / name).exists() for name in spec["expect_files"])
    return {
        "case_name": spec["case_name"],
        "input_task": spec["task"],
        "expected_tools": spec["expected_tools"],
        "final_status": final_status,
        "task_id": task_id,
        "files_changed": changed,
        "evidence_count": (state or {}).get("evidence_count", 0),
        "report_path": (state or {}).get("report_path", ""),
        "duration_seconds": duration,
        "failure_reason": (state or {}).get("failure_reason", ""),
        "event_types": event_types,
        "pass": passed,
    }


async def main() -> int:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    cases = [
        {
            "case_name": "create_text_and_summarize",
            "task": "创建 hello.txt，内容写入 matrix hello，然后读取它并生成总结报告。",
            "expected_tools": ["file"],
            "expect_files": ["hello.txt"],
        },
        {
            "case_name": "read_file_and_write_report",
            "task": "读取 source.txt 并写入 report.md 总结。",
            "files": {"source.txt": "matrix source content\n"},
            "expected_tools": ["file"],
            "expect_files": ["report.md"],
        },
        {
            "case_name": "python_version_report",
            "task": "运行 python3 --version，并把结果写入 report.md。",
            "expected_tools": ["shell", "file"],
            "expect_files": ["report.md"],
        },
        {
            "case_name": "run_success_python",
            "task": "运行 python3 main.py，并把结果写入 report.md。",
            "files": {"main.py": "print('matrix python ok')\n"},
            "expected_tools": ["shell", "file"],
            "expect_files": ["report.md"],
        },
        {
            "case_name": "repair_python_name_error",
            "task": "运行并修复 main.py，重新运行成功并写修复报告。",
            "fixture": "broken_python_project",
            "expected_tools": ["shell", "file"],
            "expect_files": ["repair_report.md"],
            "expect_event": "failure_repair",
        },
        {
            "case_name": "repair_python_import_error",
            "task": "运行并修复 main.py 的 ImportError，重新运行成功并写修复报告。",
            "fixture": "broken_python_import",
            "expected_tools": ["shell", "file"],
            "expect_files": ["repair_report.md"],
            "expect_event": "failure_repair",
        },
        {
            "case_name": "repair_python_syntax_error",
            "task": "运行并修复 main.py 的 SyntaxError，重新运行成功并写修复报告。",
            "fixture": "broken_python_syntax",
            "expected_tools": ["shell", "file"],
            "expect_files": ["repair_report.md"],
            "expect_event": "failure_repair",
        },
        {
            "case_name": "repair_node_reference_error",
            "task": "运行并修复 index.js 的 ReferenceError，重新运行成功并写修复报告。",
            "fixture": "broken_node_project",
            "expected_tools": ["shell", "file"],
            "expect_files": ["repair_report.md"],
            "expect_event": "failure_repair",
        },
        {
            "case_name": "repair_package_script",
            "task": "运行并修复 package.json 的 package script 错误，重新运行成功并写修复报告。",
            "fixture": "broken_package_script",
            "expected_tools": ["shell", "file"],
            "expect_files": ["repair_report.md"],
            "expect_event": "failure_repair",
        },
        {
            "case_name": "pending_external_ai_mock",
            "task": "执行 pending_external_ai_mock，模拟外部 AI 需要用户处理。",
            "expected_tools": [],
            "expected_status": "needs_user",
            "expect_event": "external_ai_pending_saved",
        },
    ]
    results = [await run_case(spec) for spec in cases]
    output = {
        "created_at": datetime.now().isoformat(),
        "external_ai_live_called": False,
        "results": results,
        "passed": sum(1 for result in results if result["pass"]),
        "total": len(results),
    }
    output["final_status"] = "PASS" if output["passed"] == output["total"] else "FAIL"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["final_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
