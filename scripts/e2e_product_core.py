#!/usr/bin/env python3
"""Non-live Product Core E2E against a running local backend."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from backend.api import external_ai_actions
from backend.skills.external_ai_web.pending_action import pending_external_ai_store
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.workspace_manager import WorkspaceStatus

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path("/Users/johnwick/Documents/codex/local-ai-orchestrator-core-e2e")
REPORT = ROOT / "runtime/test_reports/product_core_e2e.json"
API = "http://127.0.0.1:8422"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request_json(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        API + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with OPENER.open(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def goal(original_input: str, final_goal: str, criteria: list[str]) -> dict:
    return {
        "goal_mode": "autonomous",
        "original_input": original_input,
        "final_goal": final_goal,
        "assumptions": [],
        "user_constraints": ["只操作测试目录", "不调用外部 AI"],
        "success_criteria": criteria,
        "clarification_summary": "",
        "user_confirmed_goal": True,
        "style_preferences": [],
        "completion_standard": "满足成功标准并生成最终报告",
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
            "autonomous_visual_review": False,
            "autonomous_code_modification": False,
            "allow_sensitive_upload": False,
        },
        "user_confirmed_authorization": True,
        "denied_capabilities": ["ask_external_ai", "operate_browser"],
        "protected_paths": [],
    }


def run_task(goal_contract: dict) -> dict:
    response = request_json(
        "/api/task/start",
        {
            "goal_contract": goal_contract,
            "authorization_contract": authorization(),
        },
    )
    events = response.get("events", [])
    by_type = {}
    for event in events:
        by_type.setdefault(event.get("type"), []).append(event.get("data", {}))
    complete = (by_type.get("complete") or [{}])[-1]
    report = (by_type.get("report") or [{}])[-1].get("report", "")
    return {
        "events": events,
        "event_types": [event.get("type") for event in events],
        "task_id": complete.get("task_id", ""),
        "status": complete.get("status", ""),
        "verified": complete.get("verified", False),
        "report": report,
        "plan": (by_type.get("plan") or [{}])[-1].get("plan", {}),
        "failure_repairs": by_type.get("failure_repair", []),
    }


def main() -> int:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    for name in ("hello.txt", "report.md", "repair_report.md"):
        path = WORKSPACE / name
        if path.exists():
            path.unlink()

    task1_prompt = (
        "在测试目录里创建 hello.txt，内容写入 Local AI Orchestrator smoke test，"
        "然后读取它并生成总结报告。"
    )
    task1 = run_task(
        goal(
            task1_prompt,
            f"在 {WORKSPACE} 中创建并读取 hello.txt，然后生成总结报告。",
            ["hello.txt 存在", "hello.txt 内容正确", "生成最终报告"],
        )
    )
    hello_path = WORKSPACE / "hello.txt"
    task1.update(
        {
            "hello_exists": hello_path.exists(),
            "hello_content": hello_path.read_text(encoding="utf-8")
            if hello_path.exists()
            else "",
        }
    )
    task1["pass"] = bool(
        task1["status"] == "success"
        and task1["verified"]
        and task1["hello_content"] == "Local AI Orchestrator smoke test"
        and task1["report"]
    )

    task2_prompt = "运行 python3 --version，并把结果写入 report.md。"
    task2 = run_task(
        goal(
            task2_prompt,
            f"在 {WORKSPACE} 运行 python3 --version 并把结果写入 report.md。",
            ["记录 python3 --version stdout", "report.md 存在", "生成最终报告"],
        )
    )
    report_path = WORKSPACE / "report.md"
    task2.update(
        {
            "report_file_exists": report_path.exists(),
            "report_file_content": report_path.read_text(encoding="utf-8")
            if report_path.exists()
            else "",
        }
    )
    task2["pass"] = bool(
        task2["status"] == "success"
        and task2["verified"]
        and task2["report_file_exists"]
        and "Python" in task2["report_file_content"]
    )

    main_path = WORKSPACE / "main.py"
    main_path.write_text("print(message)\n", encoding="utf-8")
    repair_prompt = "运行这个项目，如果失败，请修复它，然后重新运行，最后写修复报告。"
    task3 = run_task(
        goal(
            repair_prompt,
            f"运行并修复 {WORKSPACE / 'main.py'}，重新运行成功并写修复报告。",
            ["识别 NameError", "main.py 修复后运行成功", "repair_report.md 存在"],
        )
    )
    repair_report = WORKSPACE / "repair_report.md"
    task3.update(
        {
            "main_content": main_path.read_text(encoding="utf-8"),
            "repair_report_exists": repair_report.exists(),
            "nameerror_detected": any(
                repair.get("failure_type") == "code_failed"
                or "NameError" in json.dumps(repair, ensure_ascii=False)
                for repair in task3["failure_repairs"]
            ),
        }
    )
    task3["pass"] = bool(
        task3["status"] == "success"
        and task3["verified"]
        and task3["nameerror_detected"]
        and "message =" in task3["main_content"]
        and task3["repair_report_exists"]
    )

    pending_task_id = "product-core-pending"
    pending_external_ai_store.save(
        task_id=pending_task_id,
        step_id="step_1",
        provider="claude",
        original_prompt="simulated prompt",
        redacted_prompt="simulated prompt",
        context={"task_id": pending_task_id, "simulation": True},
        provider_status="NEED_LOGIN",
        failure_reason="claude_profile_missing_or_not_logged_in",
        suggested_user_action="Open Claude Workspace and log in, then click Recheck/Resume",
    )
    pending_list = request_json("/api/external-ai/pending")

    class SimulatedNeedLoginWorkspace:
        async def get_workspace_status(self, provider):
            return WorkspaceStatus(
                provider="claude",
                state=ProviderState.NEED_LOGIN,
                profile_dir="runtime/browser_profiles/claude",
                page_url="",
                need_user_intervention=True,
            )

    with patch.object(
        external_ai_actions, "workspace_manager", SimulatedNeedLoginWorkspace()
    ), patch.object(
        external_ai_actions,
        "WebAISkill",
        side_effect=AssertionError("simulation must not send external AI prompt"),
    ):
        import asyncio

        resume = asyncio.run(
            external_ai_actions.resume_pending_external_ai(pending_task_id)
        )
    pending = {
        "task_id": pending_task_id,
        "pending_saved": any(
            item.get("task_id") == pending_task_id
            for item in pending_list.get("pending", [])
        ),
        "still_needs_user": resume.get("still_needs_user", False),
        "provider_status": resume.get("provider_status"),
        "failure_reason": resume.get("failure_reason"),
        "pass": bool(
            resume.get("still_needs_user")
            and resume.get("provider_status")
            in {"NEED_LOGIN", "NOT_CONFIGURED", "NEED_USER_INTERVENTION"}
        ),
    }

    output = {
        "created_at": datetime.now().isoformat(),
        "workspace": str(WORKSPACE),
        "external_ai_live_called": False,
        "task1_file": task1,
        "task2_shell": task2,
        "task3_repair": task3,
        "pending_external_ai_simulation": pending,
    }
    output["final_status"] = (
        "PASS"
        if all(
            item["pass"]
            for item in (task1, task2, task3, pending)
        )
        else "FAIL"
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["final_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
