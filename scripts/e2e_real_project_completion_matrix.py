#!/usr/bin/env python3
"""Create four isolated projects and run the durable completion loop."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.real_project_runner import RealProjectRunner

TEST_ROOT = Path(
    "/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/"
    "test-workspaces/real-project-completion-matrix"
)
REPORT = ROOT / "runtime/test_reports/real_project_completion_matrix.json"


def write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_python(root: Path) -> None:
    write(root, "README.md", "# Python CLI\nRun tests and repair the CLI.\n")
    write(root, "requirements.txt", "# standard library only\n")
    write(root, "app/__init__.py", "")
    write(root, "app/helpers.py", "def format_message(value):\n    return value.upper()\n")
    write(
        root,
        "app/core.py",
        "MISSING_IMPORT\n\ndef add(a, b):\n    LOGIC_BUG\n\ndef build_message():\n    return format_message('ready')\n",
    )
    write(root, "app/cli.py", "from .core import build_message\n\ndef main():\n    UNDEFINED_MESSAGE\n    print(message)\n")
    write(
        root,
        "tests/test_core.py",
        "import unittest\nfrom app.core import add, build_message\n\nclass T(unittest.TestCase):\n"
        "    def test_add(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_message(self): self.assertEqual(build_message(), 'READY')\n\n"
        "if __name__ == '__main__': unittest.main()\n",
    )


def create_node(root: Path) -> None:
    write(root, "README.md", "# Node project\nRepair imports and tests.\n")
    write(
        root,
        "package.json",
        '{"name":"real-node-case","version":"1.0.0","scripts":{"test":"node test.js","start":"node index.js"}}\n',
    )
    write(root, "lib/format.js", "exports.formatMessage = (value) => value.toUpperCase();\n")
    write(root, "index.js", "BROKEN_NODE_IMPORT\nUNDEFINED_NODE_VALUE\nconsole.log(value);\n")
    write(
        root,
        "test.js",
        "const { execFileSync } = require('child_process');\n"
        "const out = execFileSync('node', ['index.js'], {encoding:'utf8'}).trim();\n"
        "if (out !== 'FIXED') throw new Error(`unexpected:${out}`);\nconsole.log('node tests pass');\n",
    )


def create_react(root: Path) -> None:
    write(root, "README.md", "# React-like frontend\nRepair build and component state.\n")
    write(
        root,
        "package.json",
        '{"name":"real-react-case","version":"1.0.0","scripts":{"test":"node test.js","build":"node test.js"}}\n',
    )
    write(
        root,
        "src/App.jsx",
        "REACT_BAD_IMPORT\nexport default function App(){ return <Counter />; }\n",
    )
    write(
        root,
        "src/Counter.jsx",
        "import React, {useState} from 'react';\nexport default function Counter(){\n"
        " const [count,setCount]=useState(0);\n const increment=()=>{ REACT_STATE_BUG };\n"
        " return <button onClick={increment}>{count}</button>;\n}\n",
    )
    write(
        root,
        "test.js",
        "const fs=require('fs'); const app=fs.readFileSync('src/App.jsx','utf8');"
        " const counter=fs.readFileSync('src/Counter.jsx','utf8');"
        " if(app.includes('REACT_BAD_IMPORT')||counter.includes('REACT_STATE_BUG')) throw new Error('build failed');"
        " if(!app.includes(\"./Counter.jsx\")||!counter.includes('setCount(count + 1)')) throw new Error('logic failed');"
        " console.log('react build pass');\n",
    )


def create_mixed(root: Path) -> None:
    write(root, "README.md", "# Mixed project\nRepair backend/frontend contract.\n")
    write(root, "backend/__init__.py", "")
    write(root, "backend/service.py", "def build_message():\n    return 'mixed-ready'\n\ndef payload():\n    CROSS_MODULE_BUG\n")
    write(
        root,
        "backend/test_contract.py",
        "from service import payload\nassert payload() == {'message':'mixed-ready'}, payload()\nprint('backend pass')\n",
    )
    write(
        root,
        "frontend/app.js",
        "const payload={message:'mixed-ready'};\nAPI_FIELD_BUG\nconsole.log(message);\n",
    )
    write(
        root,
        "frontend/test.js",
        "const {execFileSync}=require('child_process'); const out=execFileSync('node',['frontend/app.js'],{encoding:'utf8'}).trim();"
        " if(out!=='mixed-ready') throw new Error(out); console.log('frontend pass');\n",
    )
    write(root, "backend/config.py", "START_CONFIG_BUG\n")


CASES = [
    (
        "case_a_python_cli",
        "python",
        create_python,
        "检查这个 Python 项目，运行测试，修复明确错误，确保程序可以运行，并生成中文修复报告。",
    ),
    (
        "case_b_node",
        "node",
        create_node,
        "检查并修复这个 Node 项目，确保 npm test 或 npm start 可以通过，并生成中文报告。",
    ),
    (
        "case_c_react",
        "react",
        create_react,
        "检查这个 React 项目，修复编译和明显功能问题，验证构建成功，并生成中文报告。",
    ),
    (
        "case_d_mixed",
        "mixed",
        create_mixed,
        "检查这个前后端项目，修复阻止运行的问题，验证前后端可以启动，并生成完整报告。",
    ),
]


def prepare() -> None:
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    for name, _, creator, _ in CASES:
        path = TEST_ROOT / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        creator(path)


def run_case(name: str, project_type: str, goal: str) -> dict:
    runner = RealProjectRunner()
    path = TEST_ROOT / name
    started = time.monotonic()
    resume_tested = name in {"case_a_python_cli", "case_d_mixed"}
    interrupt_at = 2 if resume_tested else None
    if interrupt_at:
        interrupted = runner.run(path, goal, interrupt_after_step=interrupt_at)
        result = runner.resume(interrupted["task_id"])
    else:
        result = runner.run(path, goal)
    rollback_tested = name == "case_b_node"
    rollback_success = False
    if rollback_tested:
        checkpoints = runner.list_checkpoints(result["task_id"])
        rollback_success = bool(
            checkpoints and runner.rollback(result["task_id"], checkpoints[0]["checkpoint_id"]).get("success")
        )
        result = runner.run(path, goal)
    state = runner.artifacts.read_json(result["task_id"], "task_state.json") or {}
    contract = runner.artifacts.read_json(result["task_id"], "goal_contract.json") or {}
    plan = runner.artifacts.read_json(result["task_id"], "plan.json") or {}
    return {
        "case_name": name,
        "project_type": project_type,
        **result,
        "goal_contract_created": bool(contract),
        "plan_steps": len(plan.get("plan", [])),
        "tools_used": ["file", "shell", "repair", "self_verify"],
        "verification_commands": contract.get("verification_commands", []),
        "rollback_available": bool(runner.list_checkpoints(result["task_id"])),
        "rollback_tested": rollback_tested,
        "rollback_success": rollback_success if rollback_tested else None,
        "resume_tested": resume_tested,
        "resumed_from_checkpoint": bool(state.get("resumed_from_checkpoint")),
        "completed_steps_unique": len(state.get("completed_steps", []))
        == len(set(state.get("completed_steps", []))),
        "duration_seconds": round(time.monotonic() - started, 3),
        "task_status": state.get("status"),
    }


def main() -> int:
    prepare()
    results = [run_case(name, project_type, goal) for name, project_type, _, goal in CASES]
    passed = sum(
        item["final_status"] == "PASS"
        and item["success_criteria_met"]
        and item["goal_contract_created"]
        and bool(item["report_path"])
        for item in results
    )
    output = {
        "final_status": "PASS" if passed == 4 else "PARTIAL" if passed == 3 else "FAIL",
        "passed": passed,
        "total": 4,
        "claude_call_count": sum(item["claude_call_count"] for item in results),
        "test_root": str(TEST_ROOT),
        "cases": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["final_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
