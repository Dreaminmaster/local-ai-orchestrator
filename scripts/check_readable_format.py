#!/usr/bin/env python3
"""Check that important source files are readable multi-line files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/core/agent.py": {"min_lines": 200, "max_line_len": 140},
    "backend/core/skill_router.py": {"min_lines": 80, "max_line_len": 140},
    "backend/core/failure_handler.py": {"min_lines": 40, "max_line_len": 140},
    "backend/skills/file_skill.py": {"min_lines": 120, "max_line_len": 140},
    "scripts/e2e_agent_driven_broken_project.py": {
        "min_lines": 80,
        "max_line_len": 140,
    },
}


def main() -> int:
    failures = []
    for rel, limits in CHECKS.items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"missing: {rel}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) < limits["min_lines"]:
            failures.append(
                f"{rel}: too few lines ({len(lines)} < {limits['min_lines']})"
            )
        too_long = [
            (i + 1, len(line))
            for i, line in enumerate(lines)
            if len(line) > limits["max_line_len"]
        ]
        if too_long:
            preview = ", ".join(
                f"L{line_no}:{line_len}" for line_no, line_len in too_long[:10]
            )
            failures.append(f"{rel}: long lines > {limits['max_line_len']}: {preview}")
    if failures:
        print("Readable format check failed:")
        for f in failures:
            print(" -", f)
        return 1
    print("OK: readable format check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
