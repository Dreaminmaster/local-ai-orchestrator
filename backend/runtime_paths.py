"""Runtime path helpers for dev and installed sidecar modes."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "Local AI Orchestrator"
APP_ID = "local-ai-orchestrator"


@dataclass(frozen=True)
class RuntimePaths:
    mode: str
    base_dir: Path
    runtime_dir: Path
    browser_profiles_dir: Path
    evidence_dir: Path
    test_reports_dir: Path
    playwright_browsers_path: Path
    logs_dir: Path
    tasks_dir: Path
    settings_path: Path

    def ensure(self) -> "RuntimePaths":
        for path in (
            self.base_dir,
            self.runtime_dir,
            self.browser_profiles_dir,
            self.evidence_dir,
            self.test_reports_dir,
            self.playwright_browsers_path,
            self.logs_dir,
            self.tasks_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self


def project_root_from_env(default: Path | None = None) -> Path:
    if os.environ.get("PROJECT_ROOT"):
        return Path(os.environ["PROJECT_ROOT"]).expanduser().resolve()
    return (default or Path.cwd()).expanduser().resolve()


def installed_app_data_dir(system: str | None = None, home: Path | None = None) -> Path:
    system_name = system or platform.system()
    home_dir = home or Path.home()
    if system_name == "Darwin":
        return home_dir / "Library/Application Support" / APP_NAME
    if system_name == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home_dir / "AppData/Roaming"
        return base / APP_NAME
    return home_dir / ".local/share" / APP_ID


def resolve_runtime_paths(
    *,
    project_root: Path | str | None = None,
    runtime_dir: Path | str | None = None,
    playwright_browsers_path: Path | str | None = None,
    installed: bool | None = None,
) -> RuntimePaths:
    root = Path(project_root).expanduser().resolve() if project_root else project_root_from_env()
    installed_mode = (
        installed
        if installed is not None
        else os.environ.get("LOCAL_AI_INSTALLED_MODE", "").lower() in {"1", "true", "yes"}
    )

    if runtime_dir:
        runtime = Path(runtime_dir).expanduser().resolve()
        base = runtime.parent if runtime.name == "runtime" else runtime
        mode = "custom"
    elif installed_mode:
        base = installed_app_data_dir().expanduser().resolve()
        runtime = base / "runtime"
        mode = "installed"
    else:
        base = root
        runtime = root / "runtime"
        mode = "dev"

    playwright = (
        Path(playwright_browsers_path).expanduser().resolve()
        if playwright_browsers_path
        else Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""))
        if os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        else (base / "playwright-browsers" if mode == "installed" else root / ".playwright-browsers")
    )

    return RuntimePaths(
        mode=mode,
        base_dir=base,
        runtime_dir=runtime,
        browser_profiles_dir=runtime / "browser_profiles",
        evidence_dir=runtime / "evidence",
        test_reports_dir=runtime / "test_reports",
        playwright_browsers_path=playwright,
        logs_dir=runtime / "logs",
        tasks_dir=runtime / "tasks",
        settings_path=(base / "settings.json" if mode in {"installed", "custom"} else runtime / "settings.json"),
    )
