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
    "playwright_browsers_path": "",
    "external_ai": {
        "claude": {
            "enabled": True,
            "status": "READY",
        },
        "chatgpt": {
            "enabled": True,
            "status": "NOT_CONFIGURED",
        },
    },
    "authorization_defaults": {
        "goal_strategy": "clarify_first",
        "authorization_strategy": "standard",
    },
}

SECRET_MARKERS = ("api_key", "apikey", "token", "secret", "password")


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
        if any(marker in lowered for marker in SECRET_MARKERS):
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
