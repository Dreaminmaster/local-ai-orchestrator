"""Provider state normalization for browser-based external AI."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path


PROVIDERS = ["claude", "chatgpt", "doubao", "kimi", "gemini"]
DEFAULT_PROVIDER = "claude"
FALLBACK_PROVIDER = "chatgpt"


class ProviderState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
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
    }
    return aliases.get(value, value.replace(" ", ""))


def profile_dir(provider: str, root: Path | str = "runtime/browser_profiles") -> Path:
    return Path(root) / normalize_provider(provider)


def report_path(provider: str, root: Path | str = "runtime/test_reports/web_ai") -> Path:
    return Path(root) / f"{normalize_provider(provider)}.json"


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
    if data.get("success") and quality.get("quality") == "PASS":
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
    return ProviderState.READY
