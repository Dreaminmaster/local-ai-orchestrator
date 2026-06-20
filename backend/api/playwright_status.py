"""Playwright browser provisioning status API."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body

from backend.runtime_paths import resolve_runtime_paths
from backend.settings_store import SettingsStore

router = APIRouter(tags=["playwright"])
_INSTALL = {
    "state": "idle",
    "started_at": "",
    "finished_at": "",
    "pid": None,
    "failure_reason": "",
}
_INSTALL_PROCESS: subprocess.Popen | None = None


def _chromium_found(configured_path: Path) -> bool:
    if not configured_path.exists() or not configured_path.is_dir():
        return False
    for child in configured_path.rglob("*"):
        name = child.name.lower()
        if (
            name.startswith("chromium")
            or name in {"chrome", "chrome.exe"}
            or name in {"chrome-mac", "chrome-linux", "chromium.app"}
        ):
            return True
    return False


def playwright_status_payload() -> dict:
    paths = resolve_runtime_paths(
        runtime_dir=os.environ.get("LOCAL_AI_RUNTIME_DIR") or None,
        playwright_browsers_path=os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or None,
    )
    settings = SettingsStore(paths).load()
    configured = Path(
        settings.get("playwright_browsers_path")
        or os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        or paths.playwright_browsers_path
    ).expanduser()
    chromium = _chromium_found(configured)
    if chromium:
        action = "ready"
    elif configured.exists():
        action = "需要安装项目专用浏览器；可以以后下载，不会自动下载。"
    else:
        action = "configured_path_missing; 需要安装项目专用浏览器；可以以后下载，不会自动下载。"
    return {
        "configured_path": str(configured),
        "exists": configured.exists(),
        "chromium_found": chromium,
        "recommended_action": action,
        "product_error_code": "" if chromium else "PLAYWRIGHT_BROWSER_MISSING",
        "auto_download": False,
        "estimated_download_size": "约 180-300 MB",
        "install_state": dict(_INSTALL),
    }


@router.get("/playwright/status")
async def playwright_status():
    return playwright_status_payload()


def _run_install(configured: Path, log_path: Path) -> None:
    global _INSTALL_PROCESS
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(configured)
    configured.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log_path.open("a", encoding="utf-8") as log:
            _INSTALL_PROCESS = subprocess.Popen(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
            )
            _INSTALL["pid"] = _INSTALL_PROCESS.pid
            code = _INSTALL_PROCESS.wait()
        _INSTALL["state"] = "completed" if code == 0 and _chromium_found(configured) else "failed"
        _INSTALL["failure_reason"] = "" if _INSTALL["state"] == "completed" else f"installer_exit_{code}"
    except Exception as exc:
        _INSTALL["state"] = "failed"
        _INSTALL["failure_reason"] = str(exc)
    finally:
        _INSTALL["finished_at"] = datetime.now().isoformat()
        _INSTALL["pid"] = None
        _INSTALL_PROCESS = None


@router.post("/playwright/install")
async def install_playwright_browser(payload: dict = Body(default_factory=dict)):
    if not payload.get("confirm"):
        return {
            "confirmation_required": True,
            "estimated_download_size": "约 180-300 MB",
            "install_scope": "App data / project-specific playwright-browsers only",
            "system_cache_used": False,
        }
    if _INSTALL["state"] == "running":
        return {"started": False, "install_state": dict(_INSTALL)}
    paths = resolve_runtime_paths().ensure()
    settings = SettingsStore(paths).load()
    configured = Path(settings.get("playwright_browsers_path") or paths.playwright_browsers_path).expanduser().resolve()
    log_path = paths.logs_dir / "playwright-browser-install.log"
    _INSTALL.update(state="running", started_at=datetime.now().isoformat(), finished_at="", pid=None, failure_reason="")
    threading.Thread(target=_run_install, args=(configured, log_path), daemon=True).start()
    return {
        "started": True,
        "configured_path": str(configured),
        "log_path": str(log_path),
        "install_state": dict(_INSTALL),
    }


@router.post("/playwright/install/cancel")
async def cancel_playwright_browser_install():
    if _INSTALL_PROCESS and _INSTALL_PROCESS.poll() is None:
        _INSTALL_PROCESS.terminate()
        _INSTALL["state"] = "cancelled"
        _INSTALL["failure_reason"] = "cancelled_by_user"
        return {"cancelled": True, "install_state": dict(_INSTALL)}
    return {"cancelled": False, "install_state": dict(_INSTALL)}
