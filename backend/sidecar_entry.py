"""CLI entry point for the backend sidecar prototype."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

print(
    f"[sidecar-entry] python_entry_reached pid={os.getpid()} cwd={Path.cwd()}",
    file=sys.stderr,
    flush=True,
)

from backend.runtime_paths import RuntimePaths, project_root_from_env, resolve_runtime_paths
from backend.settings_store import SettingsStore

VERSION = "0.2.1-tauri-dev-pass"


def _default_project_root() -> Path:
    return project_root_from_env(Path.cwd())


def _configure_paths(
    project_root: Path,
    paths: RuntimePaths,
) -> RuntimePaths:
    project_root = project_root.expanduser().resolve()
    paths = paths.ensure()

    os.environ["PROJECT_ROOT"] = str(project_root)
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["LOCAL_AI_RUNTIME_DIR"] = str(paths.runtime_dir)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(paths.playwright_browsers_path)
    os.environ.setdefault("DATABASE_PATH", str(paths.runtime_dir / "orchestrator.db"))
    os.environ.setdefault("PIP_CACHE_DIR", str(paths.runtime_dir / "pip_cache"))
    os.environ.setdefault("TMPDIR", str(paths.runtime_dir / "tmp"))

    (paths.runtime_dir / "tmp").mkdir(parents=True, exist_ok=True)
    SettingsStore(paths).load()

    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return paths


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
    print(
        f"[sidecar-entry] main_start argv={argv if argv is not None else sys.argv[1:]}",
        file=sys.stderr,
        flush=True,
    )
    args = _parser().parse_args(argv)

    project_root = Path(args.project_root).resolve()
    paths = resolve_runtime_paths(
        project_root=project_root,
        runtime_dir=args.runtime_dir or None,
        playwright_browsers_path=args.playwright_browsers_path or None,
    )

    _configure_paths(project_root, paths)

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
                    "runtime_dir": str(paths.runtime_dir),
                    "playwright_browsers_path": str(paths.playwright_browsers_path),
                    "runtime_mode": paths.mode,
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
        f"http://{args.host}:{args.port}",
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
