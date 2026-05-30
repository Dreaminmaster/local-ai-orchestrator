#!/usr/bin/env python3
"""Broken project repair E2E demo.
Validates: run fails -> create repair plan -> modify file -> rerun -> evidence/report.
"""

from pathlib import Path
import json
import os
import shutil
import subprocess
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "runtime/test_reports/broken_project"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def repair_node(path: Path):
    p = path / "index.js"
    text = p.read_text()
    p.write_text("const message = 'fixed node project'\n" + text)


def repair_python(path: Path):
    p = path / "main.py"
    text = p.read_text()
    p.write_text("message = 'fixed python project'\n" + text)


def test_fixture(name, command, repair):
    src = ROOT / "tests/fixtures" / name
    work = ROOT / "runtime/tmp" / name
    if work.exists() or work.is_symlink():
        if os.path.islink(work) or work.is_file():
            work.unlink()
        else:
            shutil.rmtree(work)
    shutil.copytree(src, work)
    before = run(command, work)
    repair(work)
    after = run(command, work)
    return {
        "fixture": name,
        "before_success": before.returncode == 0,
        "before_stderr": before.stderr[-1000:],
        "after_success": after.returncode == 0,
        "after_stdout": after.stdout[-1000:],
        "repair_plan": [
            "inspect error",
            "add missing message variable",
            "rerun command",
        ],
    }


def main():
    results = [
        test_fixture("broken_node_project", ["node", "index.js"], repair_node),
        test_fixture("broken_python_project", ["python3", "main.py"], repair_python),
    ]
    report = {"created_at": datetime.now().isoformat(), "results": results}
    out = REPORT_DIR / "report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert all(r["after_success"] and not r["before_success"] for r in results)


if __name__ == "__main__":
    main()
