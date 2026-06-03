"""Playwright browser provisioning status API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from backend.runtime_paths import resolve_runtime_paths
from backend.settings_store import SettingsStore

router = APIRouter(tags=["playwright"])


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
        "auto_download": False,
    }


@router.get("/playwright/status")
async def playwright_status():
    return playwright_status_payload()
