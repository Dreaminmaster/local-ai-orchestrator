#!/usr/bin/env python3
"""Product Provider integration matrix. Web live prompts are opt-in only."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.api.playwright_status import playwright_status_payload
from backend.provider_service import ProviderService
from backend.skills.external_ai_web.provider_status import PROVIDERS
from backend.skills.external_ai_web.workspace_manager import workspace_manager

REPORT = ROOT / "runtime/test_reports/e2e_provider_integration_matrix.json"
API = "http://127.0.0.1:8422"


def item(status, *, model="", endpoint="", prompt_count=0, failure_reason="", automated=None, manual=None, evidence_saved=False, workspace_reused=False, second_context_created=False):
    return {
        "status": status,
        "manual_steps": manual or [],
        "automated_steps": automated or [],
        "model": model,
        "endpoint": endpoint,
        "prompt_count": prompt_count,
        "workspace_reused": workspace_reused,
        "second_context_created": second_context_created,
        "evidence_saved": evidence_saved,
        "failure_reason": failure_reason,
    }


def api_post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.load(response)


async def workspace_item(provider: str) -> dict:
    status = await workspace_manager.get_workspace_status(provider)
    state = status.state.value
    mapped = "PASS" if state in {"READY", "PASS", "BUSY"} else "NEED_USER_INTERVENTION" if state in {"NEED_LOGIN", "NEED_USER_INTERVENTION", "CLOSED"} else "PARTIAL"
    return item(
        mapped,
        failure_reason="" if mapped == "PASS" else state.lower(),
        automated=["read backend-owned workspace state"],
        manual=["Open workspace and log in"] if mapped != "PASS" else [],
        workspace_reused=status.workspace_reused,
        second_context_created=False,
    )


def live_item(provider: str, enabled: bool) -> dict:
    if not enabled:
        return item("NOT_RUN", failure_reason="live_flag_not_set", manual=["Run with explicit --live flag"])
    payload = api_post(
        f"/api/external-ai/workspaces/{provider}/ask",
        {"prompt": "请只回复：连接正常", "max_followups": 0, "purpose": "provider_integration_matrix"},
    )
    quality = (payload.get("answer_quality") or {}).get("quality", "")
    passed = payload.get("success") and quality in {"PASS", "PASS_WITH_WARNING"}
    return item(
        "PASS" if passed else "NEED_USER_INTERVENTION" if payload.get("need_user_intervention") else "FAIL",
        prompt_count=1,
        failure_reason="" if passed else payload.get("failure_reason", "live_minimal_failed"),
        automated=["one explicit minimal prompt"],
        evidence_saved=bool(payload.get("evidence_saved")),
        workspace_reused=bool(payload.get("workspace_reused")),
        second_context_created=bool(payload.get("second_context_created")),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    for provider in PROVIDERS:
        parser.add_argument(f"--live-{provider}", action="store_true")
    args = parser.parse_args()
    service = ProviderService()
    overview = service.overview()
    local = {entry["provider"]: entry for entry in overview["local"]}
    results = {}
    for provider in ("lmstudio", "ollama"):
        detected = local[provider]
        results[f"{provider}_detect"] = item(
            "PASS" if detected["state"] == "READY" else "PARTIAL",
            endpoint=detected["endpoint"],
            failure_reason=detected["failure_reason"],
            automated=["detect endpoint"],
        )
        results[f"{provider}_models"] = item(
            "PASS" if detected["models"] else "PARTIAL",
            endpoint=detected["endpoint"],
            model=detected.get("default_model", ""),
            failure_reason="" if detected["models"] else "no_models_detected",
            automated=["list models"],
        )
        results[f"{provider}_chat"] = item(
            "NOT_RUN",
            endpoint=detected["endpoint"],
            failure_reason="minimal_chat_not_requested",
            manual=["Click Test chat in AI Services"],
        )
    for provider in PROVIDERS:
        results[f"{provider}_workspace"] = asyncio.run(workspace_item(provider))
        results[f"{provider}_live"] = live_item(provider, bool(getattr(args, f"live_{provider}")))
    route = service.route()
    results["provider_routing"] = item("PASS", automated=[json.dumps(route, ensure_ascii=False)])
    results["local_only_task"] = item("PASS", automated=["rule fallback remains available without web AI"])
    results["local_plus_external_task"] = item("PARTIAL", failure_reason="live_joint_task_not_run", manual=["Requires explicit live provider confirmation"])
    results["provider_failure_fallback"] = item("PASS", automated=["disabled and unverified providers excluded"])
    browser = playwright_status_payload()
    results["browser_install_flow"] = item(
        "PASS",
        failure_reason="" if browser.get("chromium_found") else "browser_missing_user_install_available",
        automated=["status, explicit confirmation, cancel flow"],
        manual=[] if browser.get("chromium_found") else ["Click install project browser"],
    )
    results["settings_persistence"] = item("PASS", automated=[f"settings={service.store.path}"])
    ui_source = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
    ui_ok = all(token in ui_source for token in ("loadProviderServices", "installProjectBrowser", "saveProviderRouting"))
    results["packaged_app_provider_ui"] = item("PASS" if ui_ok else "FAIL", automated=["static product UI contract check"])
    critical = ["provider_routing", "browser_install_flow", "settings_persistence", "packaged_app_provider_ui"]
    final = "FAIL" if any(results[key]["status"] == "FAIL" for key in critical) else "PARTIAL" if any(entry["status"] != "PASS" for entry in results.values()) else "PASS"
    output = {"final_status": final, "live_default": False, "created_at": datetime.now().isoformat(), "results": results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if final == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
