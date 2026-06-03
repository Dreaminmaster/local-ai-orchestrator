"""App data status, diagnostics export, and conservative cache cleanup APIs."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from backend.api.playwright_status import playwright_status_payload
from backend.runtime_paths import RuntimePaths, resolve_runtime_paths
from backend.settings_store import SettingsStore
from backend.skills.external_ai_web.provider_status import (
    PROVIDERS,
    profile_state,
)

router = APIRouter(tags=["app-data"])

SECRET_MARKERS = ("api_key", "apikey", "token", "secret", "password", "cookie")


def current_paths() -> RuntimePaths:
    return resolve_runtime_paths(
        project_root=os.environ.get("PROJECT_ROOT") or None,
        runtime_dir=os.environ.get("LOCAL_AI_RUNTIME_DIR") or None,
        playwright_browsers_path=os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or None,
    ).ensure()


def _writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def app_data_status_payload(paths: RuntimePaths | None = None) -> dict:
    paths = paths or current_paths()
    return {
        "app_data_dir": str(paths.base_dir),
        "runtime_dir": str(paths.runtime_dir),
        "logs_dir": str(paths.logs_dir),
        "settings_path": str(paths.settings_path),
        "browser_profiles_dir": str(paths.browser_profiles_dir),
        "evidence_dir": str(paths.evidence_dir),
        "test_reports_dir": str(paths.test_reports_dir),
        "playwright_browsers_path": str(paths.playwright_browsers_path),
        "exists": paths.base_dir.exists(),
        "writable": _writable(paths.base_dir),
        "mode": paths.mode,
    }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if any(marker in key.lower() for marker in SECRET_MARKERS) else _redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _provider_status() -> dict:
    return {
        provider: {
            "profile_state": profile_state(provider).value,
        }
        for provider in PROVIDERS
    }


def _safe_log_files(paths: RuntimePaths) -> list[Path]:
    if not paths.logs_dir.exists():
        return []
    allowed = []
    for path in sorted(paths.logs_dir.glob("desktop*.log"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.is_file():
            allowed.append(path)
    return allowed[:10]


def export_diagnostics(paths: RuntimePaths | None = None) -> Path:
    paths = paths or current_paths()
    diagnostics_dir = paths.base_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output = diagnostics_dir / f"local-ai-orchestrator-diagnostics-{timestamp}.zip"
    settings = _redact(SettingsStore(paths).load())
    app_data_status = app_data_status_payload(paths)
    health_snapshot = {
        "ok": True,
        "project_root": os.environ.get("PROJECT_ROOT", ""),
        "runtime_dir": str(paths.runtime_dir),
        "runtime_mode": paths.mode,
        "playwright_browsers_path": str(paths.playwright_browsers_path),
    }
    beta_report = Path(os.environ.get("PROJECT_ROOT", "")) / "BETA_VALIDATION_REPORT.md"

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("health.json", json.dumps(health_snapshot, ensure_ascii=False, indent=2))
        archive.writestr("settings.redacted.json", json.dumps(settings, ensure_ascii=False, indent=2))
        archive.writestr("provider_status.json", json.dumps(_provider_status(), ensure_ascii=False, indent=2))
        archive.writestr(
            "playwright_status.json",
            json.dumps(playwright_status_payload(), ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "app_data_status.json",
            json.dumps(app_data_status, ensure_ascii=False, indent=2),
        )
        if beta_report.is_file():
            archive.write(beta_report, "beta_validation_summary.md")
        for log_path in _safe_log_files(paths):
            archive.write(log_path, f"logs/{log_path.name}")
    return output


def _clear_directory_contents(path: Path) -> int:
    if not path.exists():
        return 0
    removed = 0
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


def clear_safe_cache(paths: RuntimePaths | None = None, keep_logs: int = 5) -> dict:
    paths = paths or current_paths()
    removed = {
        "tmp": _clear_directory_contents(paths.runtime_dir / "tmp"),
        "test_reports": _clear_directory_contents(paths.test_reports_dir),
        "pip_cache": _clear_directory_contents(paths.runtime_dir / "pip_cache"),
        "old_logs": 0,
    }
    logs = sorted(
        [path for path in paths.logs_dir.glob("*.log") if path.is_file()],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in logs[keep_logs:]:
        path.unlink()
        removed["old_logs"] += 1
    return {
        "removed": removed,
        "preserved": [
            str(paths.settings_path),
            str(paths.browser_profiles_dir),
            str(paths.evidence_dir),
            str(paths.tasks_dir),
        ],
    }


@router.get("/app-data/status")
async def app_data_status():
    return app_data_status_payload()


@router.post("/app-data/open")
async def open_app_data():
    paths = current_paths()
    if platform.system() != "Darwin":
        return {"opened": False, "reason": "open_app_data_supported_on_macos_only"}
    subprocess.Popen(["open", str(paths.base_dir)])
    return {"opened": True, "path": str(paths.base_dir)}


@router.post("/diagnostics/export")
async def diagnostics_export():
    output = export_diagnostics()
    return {"success": True, "path": str(output)}


@router.post("/app-data/clear-cache")
async def clear_cache():
    return {"success": True, **clear_safe_cache()}
