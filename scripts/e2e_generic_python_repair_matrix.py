#!/usr/bin/env python3
"""Offline matrix for generic Python repair behavior."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from backend.core.real_project_runner import RealProjectRunner


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "test-workspaces" / "generic-python-repair-matrix"
REPORT_PATH = ROOT / "runtime" / "test_reports" / "e2e_generic_python_repair_matrix.json"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def setup_case(case: dict, root: Path) -> None:
    for relative, content in case["files"].items():
        write(root / relative, content)


def classify_case(case: dict, result: dict, task_dir: Path) -> dict:
    state_path = task_dir / "task_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    report = Path(result.get("report_path", ""))
    report_text = report.read_text(encoding="utf-8") if report.exists() else ""
    files_changed = state.get("files_changed", [])
    final_status = result.get("final_status", "FAIL")
    expected = case["expected"]
    normalized_raw = "FAIL" if final_status == "FAILED" else final_status
    status_matches = (
        normalized_raw == expected
        or (expected == "NEED_USER" and final_status != "PASS")
        or (expected == "REPAIR_NOT_SUPPORTED" and final_status != "PASS")
    )
    false_success_prevented = not (
        case.get("must_not_succeed", False) and final_status == "PASS"
    )
    commands = state.get("goal_contract", {}).get("verification_commands", [])
    final = {
        "case_name": case["name"],
        "error_type": case["error_type"],
        "detected_root_cause": case["root_cause"],
        "repair_action": files_changed or ["none"],
        "files_changed": files_changed,
        "verification_command": commands[-1] if commands else "",
        "verification_exit_code": _last_exit_code(result),
        "raw_final_status": final_status,
        "final_status": expected if status_matches else final_status,
        "false_success_prevented": false_success_prevented,
        "report_path": str(report) if report else "",
        "report_mentions_runtime_failure": "运行入口仍失败" in report_text or "最终状态：失败" in report_text,
        "passed": bool(status_matches and false_success_prevented),
    }
    return final


def _last_exit_code(result: dict) -> int | None:
    task_dir = Path(result.get("_task_dir", ""))
    logs = task_dir / "step_logs.jsonl"
    if not logs.exists():
        return None
    last = None
    for line in logs.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = item.get("result") or {}
        commands = data.get("commands") or []
        if commands:
            last = commands[-1].get("exit_code")
    return last


def main() -> int:
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    cases = [
        {
            "name": "print_message_name_error",
            "error_type": "NameError",
            "root_cause": "undefined_top_level_print_name",
            "expected": "PASS",
            "files": {"main.py": "print(message)\n"},
        },
        {
            "name": "function_return_name_error",
            "error_type": "NameError",
            "root_cause": "undefined_function_return_name",
            "expected": "PASS",
            "files": {"main.py": "def build():\n    return message\n\nprint(build())\n"},
        },
        {
            "name": "wrong_local_import_module",
            "error_type": "ImportError",
            "root_cause": "local_import_module_name_mismatch",
            "expected": "PASS",
            "files": {
                "utils.py": "def build_message():\n    return 'ok'\n",
                "main.py": "from wrong_utils import build_message\nprint(build_message())\n",
            },
        },
        {
            "name": "missing_local_utils_module",
            "error_type": "ModuleNotFoundError",
            "root_cause": "missing_local_module_file",
            "expected": "NEED_USER",
            "must_not_succeed": True,
            "files": {"main.py": "from utils import build_message\nprint(build_message())\n"},
        },
        {
            "name": "package_missing_init",
            "error_type": "ImportError",
            "root_cause": "package_directory_missing_init",
            "expected": "PASS",
            "files": {
                "pkg/helpers.py": "def build_message():\n    return 'ok'\n",
                "main.py": "from pkg.helpers import build_message\nprint(build_message())\n",
            },
        },
        {
            "name": "third_party_requirement_missing",
            "error_type": "ModuleNotFoundError",
            "root_cause": "third_party_dependency_missing",
            "expected": "NEED_USER",
            "must_not_succeed": True,
            "files": {"main.py": "import definitely_missing_third_party_pkg\nprint('ok')\n"},
        },
        {
            "name": "compileall_pass_runtime_fail",
            "error_type": "RuntimeImportError",
            "root_cause": "runtime_import_inside_function",
            "expected": "FAIL",
            "must_not_succeed": True,
            "files": {"main.py": "def run():\n    import missing_runtime_pkg\n\nrun()\n"},
        },
        {
            "name": "healthy_main",
            "error_type": "None",
            "root_cause": "already_healthy",
            "expected": "PASS",
            "files": {"main.py": "print('ok')\n"},
        },
        {
            "name": "test_failure_name_error",
            "error_type": "NameError",
            "root_cause": "test_exercised_undefined_return",
            "expected": "PASS",
            "files": {
                "main.py": "def build():\n    return message\n",
                "tests/test_main.py": "import unittest\nfrom main import build\nclass T(unittest.TestCase):\n    def test_build(self): self.assertTrue(build())\n",
            },
        },
        {
            "name": "unsupported_runtime_error",
            "error_type": "RuntimeError",
            "root_cause": "unsupported_explicit_runtime_error",
            "expected": "REPAIR_NOT_SUPPORTED",
            "must_not_succeed": True,
            "files": {"main.py": "raise RuntimeError('unsupported generic failure')\n"},
        },
    ]
    results = []
    started = time.monotonic()
    for case in cases:
        project = WORK_ROOT / case["name"]
        tasks = WORK_ROOT / f"{case['name']}-tasks"
        setup_case(case, project)
        runner = RealProjectRunner(tasks)
        result = runner.run(project, f"repair {case['name']}")
        task_dir = tasks / result["task_id"]
        result["_task_dir"] = str(task_dir)
        results.append(classify_case(case, result, task_dir))
    passed = sum(1 for item in results if item["passed"])
    payload = {
        "status": "PASS" if passed >= 8 else "FAIL",
        "passed_cases": passed,
        "total_cases": len(results),
        "duration_seconds": round(time.monotonic() - started, 3),
        "report_path": str(REPORT_PATH),
        "cases": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
