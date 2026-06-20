"""User settings storage for sidecar-era local configuration."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from backend.runtime_paths import RuntimePaths, resolve_runtime_paths


DEFAULT_SETTINGS: dict[str, Any] = {
    "lmstudio_endpoint": "http://127.0.0.1:1234",
    "ollama_endpoint": "http://127.0.0.1:11434",
    "local_models": {
        "simple_mode": True,
        "default_provider": "lmstudio",
        "default_model": "",
        "roles": {
            "planner": "",
            "executor": "",
            "repair": "",
            "verifier": "",
            "summarizer": "",
        },
        "lmstudio": {
            "enabled": True,
            "endpoint": "http://127.0.0.1:1234",
            "default_model": "",
            "timeout_seconds": 120,
            "max_context": 32768,
            "temperature": 0.3,
            "max_tokens": 4096,
            "roles": ["planner", "executor", "repair", "verifier", "summarizer"],
        },
        "ollama": {
            "enabled": False,
            "endpoint": "http://127.0.0.1:11434",
            "default_model": "",
            "timeout_seconds": 120,
            "max_context": 32768,
            "temperature": 0.3,
            "max_tokens": 4096,
            "roles": [],
        },
    },
    "playwright_browsers_path": "",
    "external_ai": {
        "routing_policy": "local_first",
        "allow_automatic": False,
        "require_confirmation": True,
        "max_calls_per_task": 1,
        "onboarding_completed": False,
        "priority": ["claude", "chatgpt", "gemini", "kimi", "doubao"],
        "providers": {
            "claude": {"enabled": True, "default_model": "", "onboarding_choice": "enabled", "routing_role": "default"},
            "chatgpt": {"enabled": True, "default_model": "", "onboarding_choice": "enabled", "routing_role": "fallback"},
            "gemini": {"enabled": True, "default_model": "", "onboarding_choice": "enabled", "routing_role": "fallback"},
            "kimi": {"enabled": True, "default_model": "", "onboarding_choice": "enabled", "routing_role": "fallback"},
            "doubao": {"enabled": True, "default_model": "", "onboarding_choice": "enabled", "routing_role": "fallback"},
        },
    },
    "authorization_defaults": {
        "goal_strategy": "clarify_first",
        "authorization_strategy": "standard",
    },
}

SECRET_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "auth_token",
    "secret",
    "client_secret",
    "password",
}


def _merge_defaults(data: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_defaults(value, merged[key])
        else:
            merged[key] = value
    return merged


def _contains_secret_key(data: dict[str, Any]) -> bool:
    for key, value in data.items():
        lowered = key.lower()
        if lowered in SECRET_KEYS or lowered.endswith(("_api_key", "_password", "_secret")):
            return True
        if isinstance(value, dict) and _contains_secret_key(value):
            return True
    return False


class SettingsStore:
    def __init__(self, paths: RuntimePaths | None = None):
        self.paths = paths or resolve_runtime_paths()
        self.path: Path = self.paths.settings_path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self.create_default()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
        merged = _merge_defaults(data, DEFAULT_SETTINGS)
        if merged != data:
            self.save(merged)
        return merged

    def create_default(self) -> dict[str, Any]:
        settings = deepcopy(DEFAULT_SETTINGS)
        if not settings["playwright_browsers_path"]:
            settings["playwright_browsers_path"] = str(self.paths.playwright_browsers_path)
        self.save(settings)
        return settings

    def save(self, settings: dict[str, Any]) -> None:
        if _contains_secret_key(settings):
            raise ValueError("settings.json must not store plaintext secrets or API keys")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
