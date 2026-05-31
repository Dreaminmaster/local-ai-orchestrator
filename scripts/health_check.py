#!/usr/bin/env python3
"""Repository health check for the MVP."""

from __future__ import annotations
import importlib
import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = [
    "backend/core/agent.py",
    "backend/core/goal_interpreter.py",
    "backend/core/planner.py",
    "backend/core/capability_gap.py",
    "backend/core/skill_router.py",
    "backend/core/observer.py",
    "backend/core/verifier.py",
    "backend/core/failure_handler.py",
    "backend/core/supervisor.py",
    "backend/core/reporter.py",
    "backend/evidence/board.py",
    "backend/evidence/snapshot.py",
    "backend/security/secret_scanner.py",
    "backend/security/permissions.py",
    "backend/schemas/goal_contract.py",
    "backend/schemas/authorization_contract.py",
    "backend/core/goal_contract.py",
    "backend/core/authorization_contract.py",
    "backend/core/full_autonomy_preflight.py",
    "backend/api/contracts.py",
    "backend/api/websocket.py",
    "backend/local_model/context_manager.py",
    "backend/local_model/json_repair.py",
    "backend/local_model/prompt_builder.py",
    "backend/local_model/evidence_retriever.py",
    "backend/local_model/tool_result_summarizer.py",
    "backend/local_model/step_state.py",
    "backend/local_model/external_ai_escalation.py",
    "backend/local_model/retry_policy.py",
    "backend/local_model/local_model_runner.py",
    "backend/local_model/step_state_store.py",
    "backend/schemas/clarification_session.py",
    "backend/core/clarification_session.py",
    "backend/core/dynamic_preflight.py",
    "backend/confirmation/action_risk_classifier.py",
    "backend/browser/profile_manager.py",
    "backend/skills/external_ai_web/web_ai_skill.py",
    "backend/skills/desktop_visual/desktop_visual_skill.py",
    "backend/confirmation/queue.py",
    "backend/sandbox/workspace_manager.py",
    "backend/plugins/plugin_loader.py",
    "backend/recovery/task_checkpoint.py",
    "frontend/index.html",
    "frontend/style.css",
    "frontend/app.js",
    "scripts/check_readable_format.py",
]


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("Missing files:")
        for p in missing:
            print(" -", p)
        return 1

    for py in (ROOT / "backend").rglob("*.py"):
        if "tests/fixtures" in str(py):
            continue
        py_compile.compile(str(py), doraise=True)

    sys.path.insert(0, str(ROOT))
    imports = [
        "backend.core.agent",
        "backend.core.observer",
        "backend.core.goal_contract",
        "backend.core.authorization_contract",
        "backend.core.clarification_session",
        "backend.core.dynamic_preflight",
        "backend.api.contracts",
        "backend.evidence.snapshot",
        "backend.security.secret_scanner",
        "backend.security.permissions",
        "backend.local_model.context_manager",
        "backend.local_model.json_repair",
        "backend.local_model.evidence_retriever",
        "backend.local_model.step_state",
        "backend.local_model.retry_policy",
        "backend.local_model.local_model_runner",
        "backend.local_model.step_state_store",
        "backend.skills.desktop_visual.desktop_visual_skill",
        "backend.confirmation.queue",
        "backend.sandbox.workspace_manager",
        "backend.plugins.plugin_loader",
    ]
    for name in imports:
        importlib.import_module(name)

    readable = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_readable_format.py")],
        text=True,
        capture_output=True,
    )
    if readable.returncode != 0:
        print(readable.stdout)
        print(readable.stderr)
        return readable.returncode

    print("OK: repository health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
