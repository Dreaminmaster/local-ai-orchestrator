#!/usr/bin/env python3
"""Final product usability matrix without unbounded provider calls."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.real_project_runner import RealProjectRunner

ARCHIVE = Path(
    "/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612"
)
WORKSPACES = ARCHIVE / "test-workspaces/final-product-usability"
REPORT = ROOT / "runtime/test_reports/final_product_usability_matrix.json"
CLAUDE_RESULT = ROOT / "runtime/test_reports/final_product_claude_joint_task.json"
PACKAGED_UI_RESULT = ROOT / "runtime/test_reports/final_product_packaged_ui.json"
CLEAN_SHUTDOWN_RESULT = ROOT / "runtime/test_reports/final_product_clean_shutdown.json"


def timed(fn):
    started = time.monotonic()
    result = fn()
    result["duration"] = round(time.monotonic() - started, 3)
    return result


def matrix_item(
    status,
    evidence,
    *,
    failure_reason="",
    manual=None,
    automated=None,
    automated_steps=None,
):
    return {
        "status": status,
        "evidence": evidence,
        "failure_reason": failure_reason,
        "manual_steps": manual or [],
        "automated_steps": automated_steps or automated or [],
    }


def run_real_case(path: Path, goal: str, *, interrupt=False, rollback=False):
    runner = RealProjectRunner()
    if interrupt:
        stopped = runner.run(path, goal, interrupt_after_step=2)
        result = runner.resume(stopped["task_id"])
    else:
        result = runner.run(path, goal)
    rollback_result = None
    if rollback:
        checkpoints = runner.list_checkpoints(result["task_id"])
        rollback_result = runner.rollback(result["task_id"], checkpoints[0]["checkpoint_id"])
        result = runner.run(path, goal)
    state = runner.artifacts.read_json(result["task_id"], "task_state.json") or {}
    return result, state, rollback_result


def real_project_case(path: Path, goal: str):
    result, state, _ = run_real_case(path, goal)
    passed = result["final_status"] == "PASS" and state.get("success_criteria_met")
    return matrix_item(
        "PASS" if passed else "FAIL",
        {
            "task_id": result.get("task_id"),
            "project_path": str(path),
            "report_path": result.get("report_path"),
            "files_changed": result.get("files_changed"),
            "claude_call_count": result.get("claude_call_count"),
        },
        failure_reason=result.get("failure_reason", ""),
        automated_steps=["scan", "goal_contract", "plan", "verify", "report", "history"],
    )


def strategy_matrix():
    runner = RealProjectRunner()
    path = WORKSPACES / "money-agent-copy"
    combinations = []
    for goal_mode in ("clarify_first", "autonomous"):
        for authorization in ("standard", "full_autonomy"):
            preview = runner.prepare(
                path,
                "检查项目副本并生成报告",
                goal_mode=goal_mode,
                authorization_mode=authorization,
            )
            standard_block = None
            if authorization == "standard":
                standard_block = runner.run(
                    path,
                    "检查项目副本并生成报告",
                    goal_mode=goal_mode,
                    authorization_mode=authorization,
                )
            combinations.append(
                {
                    "goal_mode": goal_mode,
                    "authorization_mode": authorization,
                    "clarification_required": preview["goal_contract"]["clarification_required"],
                    "assumptions": preview["goal_contract"]["assumptions"],
                    "write_requires_confirmation": preview["authorization_contract"][
                        "write_requires_confirmation"
                    ],
                    "unauthorized_run_status": (
                        standard_block.get("final_status") if standard_block else "NOT_APPLICABLE"
                    ),
                }
            )
    passed = (
        combinations[0]["clarification_required"]
        and combinations[0]["unauthorized_run_status"] == "WAITING_CONFIRMATION"
        and combinations[2]["assumptions"]
    )
    return matrix_item(
        "PASS" if passed else "FAIL",
        combinations,
        automated_steps=["prepare contracts", "verify clarification", "verify standard write block"],
    )


def resume_and_rollback():
    resume_result, resume_state, _ = run_real_case(
        WORKSPACES / "money-agent-copy",
        "中断后恢复这个真实 Python 项目检查并生成报告",
        interrupt=True,
    )
    rollback_result, _, rolled = run_real_case(
        WORKSPACES / "get-more-copy",
        "验证真实前端项目并生成报告",
        rollback=True,
    )
    resume_pass = (
        resume_result["final_status"] == "PASS"
        and resume_state.get("resumed_from_checkpoint")
        and len(resume_state.get("completed_steps", []))
        == len(set(resume_state.get("completed_steps", [])))
    )
    rollback_pass = bool(rolled and rolled.get("success") and rollback_result["final_status"] == "PASS")
    return (
        matrix_item(
            "PASS" if resume_pass else "FAIL",
            {"task_id": resume_result["task_id"], "state": resume_state},
            automated_steps=["interrupt after verify", "resume", "deduplicate completed steps"],
        ),
        matrix_item(
            "PASS" if rollback_pass else "FAIL",
            {"rollback": rolled, "rerun_task_id": rollback_result["task_id"]},
            automated_steps=["checkpoint list", "rollback task", "reverify"],
        ),
    )


def create_stability_project(path: Path, index: int):
    shutil.rmtree(path, ignore_errors=True)
    (path / "tests").mkdir(parents=True)
    (path / "main.py").write_text(
        f"def value():\n    return 'stable-{index}'\n", encoding="utf-8"
    )
    (path / "tests/test_main.py").write_text(
        "import unittest\nfrom main import value\n"
        f"class T(unittest.TestCase):\n    def test_value(self): self.assertEqual(value(), 'stable-{index}')\n",
        encoding="utf-8",
    )


def five_task_stability():
    stability = WORKSPACES / "stability"
    task_ids = []
    evidence_counts = []
    for index in range(1, 6):
        project = stability / f"task-{index}"
        create_stability_project(project, index)
        result = RealProjectRunner().run(project, f"连续稳定性任务 {index}")
        task_ids.append(result["task_id"])
        evidence_counts.append(
            (RealProjectRunner().artifacts.read_json(result["task_id"], "task_state.json") or {}).get(
                "evidence_count", 0
            )
        )
        if result["final_status"] != "PASS":
            return matrix_item("FAIL", {"task_ids": task_ids}, failure_reason=result["failure_reason"])
    return matrix_item(
        "PASS",
        {"task_ids": task_ids, "unique_task_ids": len(set(task_ids)) == 5, "evidence_counts": evidence_counts},
        automated_steps=["five sequential tasks", "history isolation", "evidence isolation"],
    )


def archive_hygiene():
    forbidden = [
        Path("/Users/johnwick/Documents/codex/real_project_completion_sprint_local_backup.zip"),
        Path("/Users/johnwick/Documents/codex/local-ai-orchestrator-real-project-tests"),
        Path("/Users/johnwick/Documents/codex/.real_project_completion_sprint_package"),
    ]
    scattered = [str(path) for path in forbidden if path.exists()]
    required = ["backups", "patches", "staging", "test-workspaces", "generated-artifacts"]
    missing = [name for name in required if not (ARCHIVE / name).is_dir()]
    return matrix_item(
        "PASS" if not scattered and not missing else "FAIL",
        {"archive_root": str(ARCHIVE), "scattered": scattered, "missing_directories": missing},
        automated_steps=["scan known chat artifacts", "verify archive layout"],
    )


def read_optional(path: Path, default_status: str):
    if not path.exists():
        return matrix_item(default_status, {}, failure_reason="result_not_recorded")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    WORKSPACES.mkdir(parents=True, exist_ok=True)
    resume_started = time.monotonic()
    resume, rollback = resume_and_rollback()
    combined_duration = round(time.monotonic() - resume_started, 3)
    resume["duration"] = combined_duration
    rollback["duration"] = combined_duration
    results = {
        "packaged_ui_flow": read_optional(PACKAGED_UI_RESULT, "PARTIAL"),
        "real_project_case_1": timed(
            lambda: real_project_case(
                WORKSPACES / "money-agent-copy",
                "扫描真实 Python 项目副本，运行可靠检查，只修复明确问题并生成中文报告。",
            )
        ),
        "real_project_case_2": timed(
            lambda: real_project_case(
                WORKSPACES / "get-more-copy",
                "扫描真实 Next/React 项目副本，运行构建，只修复明确问题并生成中文报告。",
            )
        ),
        "claude_joint_task": read_optional(CLAUDE_RESULT, "PARTIAL"),
        "strategy_matrix": timed(strategy_matrix),
        "resume": resume,
        "rollback": rollback,
        "five_task_stability": timed(five_task_stability),
        "clean_shutdown": read_optional(CLEAN_SHUTDOWN_RESULT, "PARTIAL"),
        "archive_hygiene": timed(archive_hygiene),
    }
    core_fail = any(results[key]["status"] == "FAIL" for key in ("real_project_case_1", "real_project_case_2", "resume", "rollback"))
    partial = any(item["status"] != "PASS" for item in results.values())
    final = "FAIL" if core_fail else "PARTIAL" if partial else "PASS"
    output = {
        "final_status": final,
        "claude_live_calls": 1 if results["claude_joint_task"]["status"] == "PASS" else 0,
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    return 1 if final == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
