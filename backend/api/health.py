"""Health API for portable mode and desktop shell status."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from fastapi import APIRouter

from backend.skills.external_ai_web.provider_status import (
    load_provider_report,
    profile_state,
    state_from_report,
)

router = APIRouter(tags=["health"])


def _lmstudio_reachable() -> bool:
    for url in ("http://127.0.0.1:1234/v1/models", "http://localhost:1234/v1/models"):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


def _provider_health(provider: str) -> dict:
    report = load_provider_report(provider)
    report_state = (
        state_from_report(provider, report).value if report else "NOT_CONFIGURED"
    )
    pstate = profile_state(provider).value
    return {
        "profile_state": pstate,
        "test_state": report_state,
        "state": report_state if report_state != "NOT_CONFIGURED" else pstate,
        "report_available": bool(report),
    }


@router.get("/health")
async def health():
    root = Path(__file__).resolve().parents[2]
    runtime_dir = root / "runtime"
    playwright_path = Path(
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH", str(root / ".playwright-browsers"))
    )
    portable_mode = str(playwright_path).startswith(str(root)) and str(
        runtime_dir
    ).startswith(str(root))
    return {
        "ok": True,
        "backend": "running",
        "portable_mode": portable_mode,
        "project_root": str(root),
        "runtime_dir": str(runtime_dir),
        "playwright_browsers_path": str(playwright_path),
        "lmstudio_reachable": _lmstudio_reachable(),
        "external_ai": {
            "claude": _provider_health("claude"),
            "chatgpt": _provider_health("chatgpt"),
        },
    }
