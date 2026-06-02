"""CLI entry point for the backend sidecar prototype."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

VERSION = "0.2.1-tauri-dev-pass"


def _default_project_root() -> Path:
    return Path.cwd().resolve()


def _configure_paths(
    project_root: Path,
    runtime_dir: Path,
    playwright_browsers_path: Path,
) -> None:
    project_root = project_root.resolve()
    runtime_dir = runtime_dir.resolve()
    playwright_browsers_path = playwright_browsers_path.resolve()

    os.environ["PROJECT_ROOT"] = str(project_root)
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(playwright_browsers_path)
    os.environ.setdefault("PIP_CACHE_DIR", str(runtime_dir / "pip_cache"))
    os.environ.setdefault("TMPDIR", str(runtime_dir / "tmp"))

    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "tmp").mkdir(parents=True, exist_ok=True)
    (runtime_dir / "logs").mkdir(parents=True, exist_ok=True)
    (runtime_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (runtime_dir / "evidence").mkdir(parents=True, exist_ok=True)
    (runtime_dir / "test_reports").mkdir(parents=True, exist_ok=True)

    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local AI Orchestrator backend sidecar prototype"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8422, type=int)
    parser.add_argument("--project-root", default=str(_default_project_root()))
    parser.add_argument("--runtime-dir", default="")
    parser.add_argument("--playwright-browsers-path", default="")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--health-check-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    project_root = Path(args.project_root).resolve()
    runtime_dir = Path(args.runtime_dir).resolve() if args.runtime_dir else project_root / "runtime"
    playwright_path = (
        Path(args.playwright_browsers_path).resolve()
        if args.playwright_browsers_path
        else project_root / ".playwright-browsers"
    )

    _configure_paths(project_root, runtime_dir, playwright_path)

    if args.version:
        print(f"local-ai-orchestrator-backend {VERSION}")
        return 0

    if args.health_check_only:
        print(
            json.dumps(
                {
                    "ok": True,
                    "version": VERSION,
                    "project_root": str(project_root),
                    "runtime_dir": str(runtime_dir),
                    "playwright_browsers_path": str(playwright_path),
                    "env_file_embedded": False,
                    "runtime_embedded": False,
                },
                ensure_ascii=False,
            )
        )
        return 0

    from dotenv import load_dotenv
    import uvicorn

    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    from backend.main import app

    print(
        f"Local AI Orchestrator backend sidecar starting on "
        f"http://{args.host}:{args.port}"
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
