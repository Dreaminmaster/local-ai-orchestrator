"""Health API for portable mode and desktop shell status."""

from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Body

from backend.runtime_paths import resolve_runtime_paths
from backend.provider_service import ProviderService

router = APIRouter(tags=["health"])
DELIVERY_STATUS = "FINAL_PRODUCT_READY_WITH_OPTIONAL_PROVIDER_ONBOARDING"
_LMSTUDIO_CACHE = {"checked_at": 0.0, "reachable": False}
_OLLAMA_CACHE = {"checked_at": 0.0, "reachable": False}
_UI_READY = {
    "ready": False,
    "frontend_loaded": False,
    "health_panel_rendered": False,
    "desktop_shell_mode": "unknown",
    "reported_at": None,
}


def _lmstudio_reachable() -> bool:
    now = time.monotonic()
    if now - _LMSTUDIO_CACHE["checked_at"] < 10:
        return bool(_LMSTUDIO_CACHE["reachable"])
    for url in ("http://127.0.0.1:1234/v1/models", "http://localhost:1234/v1/models"):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=0.25) as resp:
                if resp.status == 200:
                    _LMSTUDIO_CACHE.update(checked_at=now, reachable=True)
                    return True
        except Exception:
            continue
    _LMSTUDIO_CACHE.update(checked_at=now, reachable=False)
    return False


def _ollama_reachable() -> bool:
    now = time.monotonic()
    if now - _OLLAMA_CACHE["checked_at"] < 10:
        return bool(_OLLAMA_CACHE["reachable"])
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=0.25) as resp:
            reachable = resp.status == 200
    except Exception:
        reachable = False
    _OLLAMA_CACHE.update(checked_at=now, reachable=reachable)
    return reachable


@router.get("/health")
async def health():
    root = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
    paths = resolve_runtime_paths(
        project_root=root,
        runtime_dir=os.environ.get("LOCAL_AI_RUNTIME_DIR") or None,
        playwright_browsers_path=os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or None,
    )
    portable_mode = (
        paths.mode == "dev"
        and str(paths.playwright_browsers_path).startswith(str(root))
        and str(paths.runtime_dir).startswith(str(root))
    )
    providers = ProviderService().overview()
    return {
        "ok": True,
        "delivery_status": DELIVERY_STATUS,
        "backend": "running",
        "portable_mode": portable_mode,
        "project_root": str(root),
        "runtime_dir": str(paths.runtime_dir),
        "runtime_mode": paths.mode,
        "playwright_browsers_path": str(paths.playwright_browsers_path),
        "lmstudio_reachable": _lmstudio_reachable(),
        "ollama_reachable": _ollama_reachable(),
        "local_models": {item["provider"]: item for item in providers["local"]},
        "external_ai": {item["provider"]: item for item in providers["web"]},
    }


@router.get("/ui-ready")
async def ui_ready():
    return dict(_UI_READY)


@router.post("/ui-ready")
async def report_ui_ready(payload: dict = Body(default_factory=dict)):
    _UI_READY.update(
        ready=bool(payload.get("ready")),
        frontend_loaded=bool(payload.get("frontend_loaded")),
        health_panel_rendered=bool(payload.get("health_panel_rendered")),
        desktop_shell_mode=str(payload.get("desktop_shell_mode") or "unknown"),
        reported_at=time.time(),
    )
    print(
        "[ui-ready] "
        f"ready={_UI_READY['ready']} "
        f"frontend_loaded={_UI_READY['frontend_loaded']} "
        f"health_panel_rendered={_UI_READY['health_panel_rendered']} "
        f"desktop_shell_mode={_UI_READY['desktop_shell_mode']}"
    )
    return dict(_UI_READY)
