"""User Preferences — Long-term user preference storage."""
from __future__ import annotations
import json
from pathlib import Path


class UserPreferences:
    """Stores and retrieves user preferences."""

    def __init__(self, db=None):
        self.db = db
        self._cache: dict[str, str] = {}

    async def set(self, key: str, value: str):
        self._cache[key] = value
        if self.db:
            await self.db.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                [key, value],
            )

    async def get(self, key: str, default: str = "") -> str:
        if key in self._cache:
            return self._cache[key]
        if self.db:
            row = await self.db.fetch_one("SELECT value FROM user_preferences WHERE key = ?", [key])
            if row:
                self._cache[key] = row["value"]
                return row["value"]
        return default

    async def get_all(self) -> dict[str, str]:
        if self.db:
            rows = await self.db.fetch_all("SELECT key, value FROM user_preferences")
            for r in rows:
                self._cache[r["key"]] = r["value"]
        return dict(self._cache)

    async def get_context(self) -> str:
        """Get preferences as text for LLM context."""
        prefs = await self.get_all()
        if not prefs:
            return "No user preferences set."
        lines = [f"- {k}: {v}" for k, v in prefs.items()]
        return "\n".join(lines)
