#!/usr/bin/env python3
"""Offline/API smoke for the Provider Workspace Console."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8422/api"
REPORT = Path("runtime/test_reports/e2e_provider_workspace_console.json")


def request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode("utf-8") if method != "GET" else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    started = time.monotonic()
    checks: list[dict] = []
    final_status = "PASS"

    def add(name: str, passed: bool, detail: dict | str = "") -> None:
        nonlocal final_status
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            final_status = "FAIL"

    try:
        console = request("/web-ai/workspaces/console")
        providers = console.get("providers", {})
        add(
            "console_lists_all_main_web_providers",
            all(name in providers for name in ["claude", "chatgpt", "gemini", "kimi", "doubao"]),
            {"providers": sorted(providers)},
        )
        for name, item in providers.items():
            add(
                f"{name}_has_state_and_profile",
                bool(item.get("workspace_state") or item.get("state")) and "profile_dir" in item,
                {
                    "workspace_state": item.get("workspace_state"),
                    "profile_dir": item.get("profile_dir"),
                },
            )
        add(
            "console_summary_counts_present",
            {"enabled_count", "logged_in_count", "route_ready_count", "active_provider"}.issubset(console),
            console,
        )
    except urllib.error.URLError as exc:
        add("backend_reachable", False, str(exc))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "final_status": final_status,
        "duration_seconds": round(time.monotonic() - started, 3),
        "checks": checks,
        "notes": [
            "This script does not send live provider prompts.",
            "Window focus/open behavior is covered by backend open/status APIs and manual packaged App smoke.",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

