"""Provider state normalization for browser-based external AI."""

from __future__ import annotations

import json
import os
from enum import StrEnum
from pathlib import Path

from backend.runtime_paths import resolve_runtime_paths


PROVIDERS = ["claude", "chatgpt", "doubao", "kimi", "gemini"]
DEFAULT_PROVIDER = "claude"
FALLBACK_PROVIDER = "chatgpt"


class ProviderState(StrEnum):
    INSTALL_REQUIRED = "INSTALL_REQUIRED"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"
    CLOSED = "CLOSED"
    OPENING = "OPENING"
    OPEN = "OPEN"
    BUSY = "BUSY"
    CRASHED = "CRASHED"
    PAGE_ERROR = "PAGE_ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NEED_LOGIN = "NEED_LOGIN"
    READY = "READY"
    STALE_CONVERSATION = "STALE_CONVERSATION"
    PAGE_NETWORK_ERROR = "PAGE_NETWORK_ERROR"
    RETRYABLE_PAGE_ERROR = "RETRYABLE_PAGE_ERROR"
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    NEED_USER_INTERVENTION = "NEED_USER_INTERVENTION"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


def normalize_provider(provider: str) -> str:
    value = (provider or "").strip().lower().replace("_", " ")
    aliases = {
        "claude web": "claude",
        "chatgpt web": "chatgpt",
        "openai chatgpt": "chatgpt",
        "gemini web": "gemini",
        "kimi web": "kimi",
        "doubao web": "doubao",
        "豆包 web": "doubao",
    }
    return aliases.get(value, value.replace(" ", ""))


def _runtime_paths():
    return resolve_runtime_paths(
        project_root=os.environ.get("PROJECT_ROOT") or None,
        runtime_dir=os.environ.get("LOCAL_AI_RUNTIME_DIR") or None,
        playwright_browsers_path=os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or None,
    )


def profile_dir(provider: str, root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _runtime_paths().browser_profiles_dir
    return base / normalize_provider(provider)


def report_path(provider: str, root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _runtime_paths().test_reports_dir / "web_ai"
    return base / f"{normalize_provider(provider)}.json"


def load_provider_report(provider: str) -> dict:
    path = report_path(provider)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"success": False, "error": "unreadable_report"}


def state_from_report(provider: str, report: dict | None = None) -> ProviderState:
    data = report if report is not None else load_provider_report(provider)
    if not data:
        return ProviderState.NOT_CONFIGURED
    quality = data.get("answer_quality") or {}
    if data.get("success") and quality.get("quality") in {"PASS", "PASS_WITH_WARNING"}:
        return ProviderState.PASS
    if data.get("login_detection") and (
        data.get("send_prompt") or data.get("extract_answer") or data.get("evidence_saved")
    ):
        return ProviderState.PARTIAL
    if data.get("needs_login") or data.get("failure_stage") == "login":
        return ProviderState.NEED_LOGIN
    return ProviderState.FAIL


def profile_state(provider: str) -> ProviderState:
    pdir = profile_dir(provider)
    if not pdir.exists() or not any(pdir.iterdir()):
        return ProviderState.NOT_CONFIGURED
    # A persistent profile directory proves only that the provider was opened
    # before. Login state must be verified from an active provider page.
    return ProviderState.NEED_LOGIN
