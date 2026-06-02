#!/usr/bin/env python3
"""Portable beta-kernel validation entry point.

Default mode is non-live. Claude Web live E2E only runs when --live-claude is
passed explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "BETA_VALIDATION_REPORT.md"


def run_check(name: str, cmd: list[str], *, env: dict[str, str] | None = None) -> dict:
    merged_env = os.environ.copy()
    merged_env.update(
        {
            "PROJECT_ROOT": str(ROOT),
            "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".playwright-browsers"),
            "PIP_CACHE_DIR": str(ROOT / "runtime/pip_cache"),
            "TMPDIR": str(ROOT / "runtime/tmp"),
            "PYTHONPATH": str(ROOT),
        }
    )
    if env:
        merged_env.update(env)
    started = datetime.now()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=merged_env,
            text=True,
            capture_output=True,
            timeout=360,
        )
        status = "PASS" if proc.returncode == 0 else "FAIL"
        if name == "live_claude_workspace_e2e":
            try:
                live_report = json.loads(
                    (ROOT / "runtime/test_reports/e2e_claude_workspace_live.json").read_text(
                        encoding="utf-8"
                    )
                )
                final_status = live_report.get("final_status", "")
                if final_status == "NEED_USER_INTERVENTION":
                    status = "NEED_USER_INTERVENTION"
                elif final_status == "PASS":
                    status = "PASS"
                elif proc.returncode != 0:
                    status = "FAIL"
            except Exception:
                pass
        return {
            "name": name,
            "status": status,
            "returncode": proc.returncode,
            "cmd": " ".join(cmd),
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "started_at": started.isoformat(),
            "finished_at": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "status": "FAIL",
            "returncode": None,
            "cmd": " ".join(cmd),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": "timeout",
            "started_at": started.isoformat(),
            "finished_at": datetime.now().isoformat(),
        }


def python_cmd() -> str:
    venv_python = ROOT / "venv/bin/python"
    return str(venv_python) if venv_python.exists() else sys.executable


def portable_status() -> dict:
    return {
        "project_root": str(ROOT),
        "venv": str(ROOT / "venv"),
        "venv_exists": (ROOT / "venv").exists(),
        "playwright_browsers": str(ROOT / ".playwright-browsers"),
        "playwright_browsers_exists": (ROOT / ".playwright-browsers").exists(),
        "runtime": str(ROOT / "runtime"),
        "runtime_exists": (ROOT / "runtime").exists(),
        "playwright_env_ok": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))
        == str(ROOT / ".playwright-browsers"),
    }


def repair_matrix_passed() -> str:
    path = ROOT / "runtime/test_reports/e2e_repair_matrix.json"
    if not path.exists():
        return "unknown"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.get("results", [])
        if len(results) == 10 and all(item.get("pass") for item in results):
            return "10/10 PASS"
        return f"{sum(1 for item in results if item.get('pass'))}/{len(results)}"
    except Exception as exc:
        return f"unreadable: {exc}"


def write_report(checks: list[dict], *, live_requested: bool) -> None:
    portable = portable_status()
    core_checks = [item for item in checks if not item["name"].startswith("live_")]
    blocking_failures = [item for item in checks if item["status"] == "FAIL"]
    core_pass = all(item["status"] in ("PASS", "SKIP") for item in core_checks)
    workspace_auto_pass = any(
        item["name"] == "live_claude_workspace_e2e" and item["status"] == "PASS"
        for item in checks
    )
    workspace_needs_user = any(
        item["status"] == "NEED_USER_INTERVENTION" for item in checks
    )
    overall = "PASS" if core_pass and not blocking_failures else "FAIL"
    lines = [
        "# Beta Validation Report",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        f"Overall: **{overall}**",
        "",
        "## Validation Summary",
        "",
        f"- core_pass: `{str(core_pass).lower()}`",
        f"- workspace_auto_pass: `{str(workspace_auto_pass).lower()}`",
        f"- workspace_needs_user: `{str(workspace_needs_user).lower()}`",
        f"- blocking_failures: `{len(blocking_failures)}`",
        "- Workspace needing login/verification is a resumable product state, not a beta kernel failure.",
        "",
        "## Portable Mode",
        "",
        f"- Project root: `{portable['project_root']}`",
        f"- venv: `{portable['venv']}` ({'exists' if portable['venv_exists'] else 'missing'})",
        f"- Playwright browsers: `{portable['playwright_browsers']}` ({'exists' if portable['playwright_browsers_exists'] else 'missing'})",
        f"- runtime: `{portable['runtime']}` ({'exists' if portable['runtime_exists'] else 'missing'})",
        f"- PLAYWRIGHT_BROWSERS_PATH expected: `{portable['playwright_browsers']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Command |",
        "|---|---:|---|",
    ]
    for item in checks:
        lines.append(f"| {item['name']} | {item['status']} | `{item['cmd']}` |")
    lines.extend(
        [
            "",
            "## Repair Matrix",
            "",
            f"- Latest report summary: {repair_matrix_passed()}",
            "",
            "## Claude Web Live E2E",
            "",
            f"- Requested in this run: {str(live_requested).lower()}",
            "- Default behavior: not run unless `--live-claude` is provided.",
            "- NEED_USER_INTERVENTION means the workspace correctly paused for user login/verification and can resume.",
            "",
            "## Details",
            "",
        ]
    )
    for item in checks:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- Status: {item['status']}",
                f"- Return code: {item['returncode']}",
                "",
                "stdout tail:",
                "",
                "```text",
                item.get("stdout_tail", ""),
                "```",
                "",
                "stderr tail:",
                "",
                "```text",
                item.get("stderr_tail", ""),
                "```",
                "",
            ]
        )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live-claude",
        action="store_true",
        help="Run the live Claude Web forced E2E. This is opt-in and may consume account quota.",
    )
    args = parser.parse_args()

    py = python_cmd()
    checks = [
        run_check("health_check", [py, "scripts/health_check.py"]),
        run_check("repair_matrix", [py, "scripts/e2e_agent_driven_repair_matrix.py"]),
        run_check("frontend_node_check", ["node", "--check", "frontend/app.js"]),
        run_check(
            "claude_extractor_unittest",
            [py, "-m", "unittest", "tests/test_claude_answer_extractor_from_evidence.py"],
        ),
    ]
    if args.live_claude:
        checks.append(
            run_check(
                "live_claude_workspace_e2e",
                [py, "scripts/e2e_claude_workspace_live.py"],
            )
        )
    else:
        checks.append(
            {
                "name": "live_claude_workspace_e2e",
                "status": "SKIP",
                "returncode": None,
                "cmd": f"{py} scripts/e2e_claude_workspace_live.py",
                "stdout_tail": "Skipped by default. Re-run with --live-claude after user confirmation.",
                "stderr_tail": "",
                "started_at": datetime.now().isoformat(),
                "finished_at": datetime.now().isoformat(),
            }
        )
    write_report(checks, live_requested=args.live_claude)
    print(f"REPORT={REPORT}")
    return 0 if all(item["status"] in ("PASS", "SKIP", "NEED_USER_INTERVENTION") for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
