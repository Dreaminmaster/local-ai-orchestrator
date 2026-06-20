#!/usr/bin/env python3
"""Open a provider profile through the backend-owned workspace."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "runtime/test_reports/web_ai/profile_status.json"
API_BASE = "http://127.0.0.1:8422/api"
PROVIDERS = ["chatgpt", "claude", "doubao", "gemini", "kimi"]


def request(path: str, method: str = "GET") -> dict:
    req = urllib.request.Request(f"{API_BASE}{path}", method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open a backend-owned Web AI persistent workspace"
    )
    parser.add_argument("--provider", required=True, choices=PROVIDERS)
    args = parser.parse_args()

    print(f"Opening backend-owned {args.provider} workspace.")
    print("The backend must be running. This script never opens a second browser context.")
    status = request(f"/web-ai/workspace/{args.provider}/open", "POST")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    input("Log in or handle the provider page, then press Enter to recheck...\n")
    status = request(f"/web-ai/workspace/{args.provider}/status")
    status.update(
        {
            "logged_in": status.get("state") == "READY",
            "initialized_at": datetime.now().isoformat(),
            "profile_owner": "backend",
            "second_context_created": False,
        }
    )

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if STATUS_PATH.exists():
        existing = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    existing[args.provider] = status
    STATUS_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["logged_in"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
