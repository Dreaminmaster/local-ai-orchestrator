#!/usr/bin/env python3
"""Repository health check for the MVP."""
from __future__ import annotations
import importlib
import pathlib
import py_compile
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
    "backend/security/permissions.py",
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
]


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("Missing files:")
        for p in missing:
            print(" -", p)
        return 1

    for py in (ROOT / "backend").rglob("*.py"):
        py_compile.compile(str(py), doraise=True)

    sys.path.insert(0, str(ROOT))
    imports = [
        "backend.core.agent",
        "backend.core.observer",
        "backend.evidence.snapshot",
        "backend.security.permissions",
        "backend.skills.external_ai_web.web_ai_skill",
        "backend.skills.desktop_visual.desktop_visual_skill",
        "backend.confirmation.queue",
        "backend.sandbox.workspace_manager",
        "backend.plugins.plugin_loader",
    ]
    for name in imports:
        importlib.import_module(name)

    print("OK: repository health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
