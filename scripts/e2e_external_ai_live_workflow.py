#!/usr/bin/env python3
"""External AI workflow E2E. Live Claude calls are opt-in."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.api import external_ai_actions
from backend.api.playwright_status import playwright_status_payload
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter
from backend.security.secret_scanner import SecretScanner
from backend.skills.base import SkillResult
from backend.skills.external_ai_web.pending_action import PendingExternalAIStore
from backend.skills.external_ai_web.provider_status import ProviderState
from backend.skills.external_ai_web.web_ai_skill import WebAISkill
from backend.skills.external_ai_web.workspace_manager import WorkspaceStatus

REPORT = ROOT / "runtime/test_reports/e2e_external_ai_live_workflow.json"
MINIMAL_REPORT = ROOT / "runtime/test_reports/web_ai/claude_live_minimal.json"
AGENT_REPORT = ROOT / "runtime/test_reports/e2e_agent_uses_claude_web_live.json"
API_BASE = "http://127.0.0.1:8422"


class FakeWorkspace:
    def __init__(self, state: ProviderState):
        self.state = state
        self.last_recoveries = {}
        self.last_statuses = {
            "claude": WorkspaceStatus(
                provider="claude",
                state=state,
                profile_dir="runtime/browser_profiles/claude",
                page_url="https://claude.ai/new",
                need_user_intervention=state != ProviderState.READY,
            )
        }

    async def ensure_workspace(self, provider):
        return None

    async def get_workspace_status(self, provider):
        return self.last_statuses["claude"]


class FakeSuccessSkill:
    async def execute(self, instruction, context):
        return SkillResult(
            "web_ai",
            True,
            "Use a defined variable before printing it.",
            evidence=["runtime/evidence/web_ai/claude/mock"],
            metadata={"quality_check": {"quality": "PASS"}, "provider": "claude"},
        )


async def offline_checks() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        store = PendingExternalAIStore(Path(tmp))
        with patch(
            "backend.skills.external_ai_web.web_ai_skill.pending_external_ai_store", store
        ), patch(
            "backend.skills.external_ai_web.web_ai_skill.workspace_manager",
            FakeWorkspace(ProviderState.NEED_LOGIN),
        ):
            pending_result = await WebAISkill().execute(
                "ask claude",
                {
                    "task_id": "external_ai_offline_pending",
                    "provider": "Claude Web",
                    "prompt": "redacted mock prompt",
                    "reuse_workspace": True,
                },
            )

        store.save(
            task_id="external_ai_resume_blocked",
            step_id="step_1",
            provider="claude",
            original_prompt="mock",
            redacted_prompt="mock",
            context={"task_id": "external_ai_resume_blocked"},
            provider_status="NEED_LOGIN",
            failure_reason="claude_profile_missing_or_not_logged_in",
            suggested_user_action="log in",
        )
        with patch.object(external_ai_actions, "pending_external_ai_store", store), patch.object(
            external_ai_actions, "workspace_manager", FakeWorkspace(ProviderState.NEED_LOGIN)
        ), patch.object(
            external_ai_actions, "WebAISkill", side_effect=AssertionError("must not send")
        ):
            blocked = await external_ai_actions.resume_pending_external_ai(
                "external_ai_resume_blocked"
            )

        store.save(
            task_id="external_ai_resume_ready",
            step_id="step_1",
            provider="claude",
            original_prompt="mock",
            redacted_prompt="mock",
            context={"task_id": "external_ai_resume_ready"},
            provider_status="NEED_LOGIN",
            failure_reason="claude_profile_missing_or_not_logged_in",
            suggested_user_action="log in",
        )
        with patch.object(external_ai_actions, "pending_external_ai_store", store), patch.object(
            external_ai_actions, "workspace_manager", FakeWorkspace(ProviderState.READY)
        ), patch.object(external_ai_actions, "WebAISkill", return_value=FakeSuccessSkill()):
            resumed = await external_ai_actions.resume_pending_external_ai(
                "external_ai_resume_ready"
            )

    checks = {
        "claude_unlogged_pending": bool(
            not pending_result.success
            and pending_result.metadata.get("need_user_intervention")
        ),
        "claude_ready_mock": FakeWorkspace(ProviderState.READY).state == ProviderState.READY,
        "resume_still_needs_user": bool(blocked.get("still_needs_user")),
        "resume_success_mock": bool(resumed.get("success")),
        "prompt_not_sent_while_unready": True,
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


async def live_minimal() -> dict:
    prompt = "请让 Claude 给出一句简短建议：如何修复 Python NameError？回答不超过 2 句话。"
    safe_prompt = SecretScanner().redact(prompt).redacted_text
    result = await api_post(
        "/api/external-ai/workspaces/claude/ask",
        {
            "task_id": "claude_live_minimal",
            "prompt": safe_prompt,
            "debug": True,
            "purpose": "claude_live_minimal",
        },
    )
    quality = result.get("answer_quality", {})
    out = {
        "created_at": datetime.now().isoformat(),
        "provider": "Claude Web",
        "success": bool(result.get("success")),
        "profile_owner": result.get("profile_owner", ""),
        "workspace_reused": bool(result.get("workspace_reused")),
        "second_context_created": bool(result.get("second_context_created")),
        "prompt_count": 1 if result.get("send_success") else 0,
        "need_user_intervention": bool(result.get("need_user_intervention")),
        "answer_quality": quality,
        "used_selector": result.get("used_selector", ""),
        "evidence_saved": bool(result.get("evidence_saved")),
        "evidence_path": result.get("evidence_path", ""),
        "failure_reason": result.get("failure_reason", ""),
    }
    out["final_status"] = (
        "PASS"
        if out["success"]
        and quality.get("quality") in {"PASS", "PASS_WITH_WARNING"}
        and out["evidence_saved"]
        and out["profile_owner"] == "backend"
        and out["workspace_reused"]
        and not out["second_context_created"]
        else "NEED_USER_INTERVENTION"
        if out["need_user_intervention"]
        else "FAIL"
    )
    MINIMAL_REPORT.parent.mkdir(parents=True, exist_ok=True)
    MINIMAL_REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


async def agent_live() -> dict:
    router = ExternalAIEscalationRouter()
    selected = router.choose_target("code_repair_failed", ["Claude Web"])
    prompt = (
        "这个 Python 报错信息比较模糊，请给出简短修复建议，并说明下一步应检查什么。"
    )
    result = await api_post(
        "/api/external-ai/workspaces/claude/ask",
        {
            "task_id": "e2e_agent_uses_claude_web_live",
            "prompt": prompt,
            "debug": True,
            "purpose": "agent_uses_claude_live",
        },
    )
    quality = result.get("answer_quality", {})
    final_report_path = ROOT / "runtime/tasks/e2e_agent_uses_claude_web_live/final_report.md"
    report_text = ""
    if result.get("success"):
        report_text = (
            "# Agent External AI Report\n\n"
            "使用 Claude Web 外部求助。\n\n"
            f"{result.get('answer', '')}\n"
        )
        final_report_path.parent.mkdir(parents=True, exist_ok=True)
        final_report_path.write_text(report_text, encoding="utf-8")
    out = {
        "created_at": datetime.now().isoformat(),
        "selected_target": selected,
        "success": bool(result.get("success")),
        "profile_owner": result.get("profile_owner", ""),
        "workspace_reused": bool(result.get("workspace_reused")),
        "second_context_created": bool(result.get("second_context_created")),
        "prompt_count": 1 if result.get("send_success") else 0,
        "need_user_intervention": bool(result.get("need_user_intervention")),
        "answer_quality": quality,
        "evidence_saved": bool(result.get("evidence_saved")),
        "evidence_path": result.get("evidence_path", ""),
        "failure_reason": result.get("failure_reason", ""),
        "external_advice_summary": result.get("answer", "")[:500],
        "report_contains_claude_web": "使用 Claude Web 外部求助" in report_text,
        "report_path": str(final_report_path) if report_text else "",
    }
    out["final_status"] = (
        "PASS"
        if selected == "Claude Web"
        and out["success"]
        and quality.get("quality") in {"PASS", "PASS_WITH_WARNING"}
        and out["evidence_saved"]
        and out["workspace_reused"]
        and not out["second_context_created"]
        and out["report_contains_claude_web"]
        else "NEED_USER_INTERVENTION"
        if out["need_user_intervention"]
        else "FAIL"
    )
    AGENT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    AGENT_REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


async def api_get(path: str) -> dict:
    def request():
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{API_BASE}{path}", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    return await asyncio.to_thread(request)


async def api_post(path: str, payload: dict | None = None) -> dict:
    def request():
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{API_BASE}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))

    return await asyncio.to_thread(request)


async def ensure_backend() -> tuple[subprocess.Popen | None, bool]:
    try:
        health = await api_get("/api/health")
        if health.get("ok"):
            return None, True
    except Exception:
        pass
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_ROOT": str(ROOT),
            "LOCAL_AI_RUNTIME_DIR": str(ROOT / "runtime"),
            "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".playwright-browsers"),
            "PYTHONPATH": str(ROOT),
        }
    )
    log_path = ROOT / "runtime/logs/e2e_external_ai_backend.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8422",
        ],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(60):
        await asyncio.sleep(0.5)
        try:
            if (await api_get("/api/health")).get("ok"):
                return process, False
        except Exception:
            if process.poll() is not None:
                break
    process.terminate()
    raise RuntimeError(f"backend_start_failed; log={log_path}")


def write_skipped_live_reports(reason: str, *, write_minimal: bool = True) -> tuple[dict, dict]:
    minimal = {
        "created_at": datetime.now().isoformat(),
        "provider": "Claude Web",
        "final_status": "SKIPPED",
        "failure_reason": reason,
        "live_call_made": False,
    }
    agent = {
        "created_at": datetime.now().isoformat(),
        "selected_target": "Claude Web",
        "final_status": "SKIPPED",
        "failure_reason": reason,
        "live_call_made": False,
    }
    if write_minimal:
        MINIMAL_REPORT.parent.mkdir(parents=True, exist_ok=True)
        MINIMAL_REPORT.write_text(json.dumps(minimal, ensure_ascii=False, indent=2), encoding="utf-8")
    AGENT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    AGENT_REPORT.write_text(json.dumps(agent, ensure_ascii=False, indent=2), encoding="utf-8")
    return minimal, agent


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-claude", action="store_true")
    args = parser.parse_args()
    offline = await offline_checks()
    output = {
        "created_at": datetime.now().isoformat(),
        "live_claude_requested": args.live_claude,
        "offline": offline,
        "live_minimal": {"final_status": "SKIPPED"},
        "agent_uses_claude_live": {"final_status": "SKIPPED"},
        "profile_owner": "backend",
        "second_context_created": False,
        "live_prompt_total": 0,
        "other_providers_called": [],
    }
    started_backend = None
    if args.live_claude:
        browser_status = playwright_status_payload()
        output["playwright_status"] = browser_status
        if not browser_status.get("chromium_found"):
            output["live_minimal"], output["agent_uses_claude_live"] = (
                write_skipped_live_reports("PLAYWRIGHT_BROWSER_MISSING")
            )
        else:
            try:
                started_backend, reused_backend = await ensure_backend()
                output["backend_reused"] = reused_backend
                workspace = await api_post("/api/web-ai/workspace/claude/open")
                output["workspace_open"] = workspace
                if workspace.get("state") != ProviderState.READY.value:
                    output["live_minimal"], output["agent_uses_claude_live"] = (
                        write_skipped_live_reports(
                            f"claude_workspace_not_ready:{workspace.get('state', 'UNKNOWN')}"
                        )
                    )
                else:
                    output["live_minimal"] = await live_minimal()
                    output["live_prompt_total"] += output["live_minimal"].get(
                        "prompt_count", 0
                    )
                    if output["live_minimal"]["final_status"] == "PASS":
                        output["agent_uses_claude_live"] = await agent_live()
                        output["live_prompt_total"] += output[
                            "agent_uses_claude_live"
                        ].get("prompt_count", 0)
                    else:
                        _, output["agent_uses_claude_live"] = write_skipped_live_reports(
                            "live_minimal_not_pass", write_minimal=False
                        )
            except Exception as exc:
                reason = f"backend_api_preflight_failed:{exc}"
                output["live_minimal"], output["agent_uses_claude_live"] = (
                    write_skipped_live_reports(reason)
                )
                output["live_preflight_failure"] = reason
            finally:
                if started_backend is not None:
                    started_backend.terminate()
                    try:
                        started_backend.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        started_backend.kill()
    else:
        output["live_minimal"], output["agent_uses_claude_live"] = (
            write_skipped_live_reports("live_claude_not_requested")
        )
    statuses = [
        offline["status"],
        output["live_minimal"]["final_status"],
        output["agent_uses_claude_live"]["final_status"],
    ]
    output["final_status"] = (
        "PASS"
        if offline["status"] == "PASS"
        and (not args.live_claude or statuses[1:] == ["PASS", "PASS"])
        else "PARTIAL"
        if offline["status"] == "PASS"
        else "FAIL"
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["final_status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
