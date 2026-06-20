"""Web AI profile management API."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body

from backend.runtime_paths import resolve_runtime_paths
from backend.api.playwright_status import playwright_status_payload
from backend.skills.external_ai_web.provider_status import (
    PROVIDERS,
    ProviderState,
    normalize_provider,
    profile_state,
    state_from_report,
)
from backend.skills.external_ai_web.workspace_manager import workspace_manager
from backend.skills.external_ai_web.web_ai_skill import WebAISkill

router = APIRouter(tags=["web-ai-profiles"])

def _paths():
    return resolve_runtime_paths(
        project_root=os.environ.get("PROJECT_ROOT") or None,
        runtime_dir=os.environ.get("LOCAL_AI_RUNTIME_DIR") or None,
        playwright_browsers_path=os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or None,
    ).ensure()


def _profile_dir() -> Path:
    return _paths().browser_profiles_dir


def _test_report_dir() -> Path:
    return _paths().test_reports_dir / "web_ai"


def _status_path() -> Path:
    return _test_report_dir() / "profile_status.json"


def _load_status():
    path = _status_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _test_report_path(provider: str) -> Path:
    return _test_report_dir() / f"{provider}.json"


def _recommendation(provider: str, test_status: str) -> str:
    if provider == "claude" and test_status == "PASS":
        return "推荐使用"
    if provider == "chatgpt" and test_status == "PARTIAL":
        return "可用但不稳定"
    if test_status == "FAIL":
        return "需要重新测试"
    return ""


def _load_report(provider: str) -> dict:
    path = _test_report_path(provider)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"provider": provider, "success": False, "error": str(exc)}


def _quality_issues(report: dict) -> list[str]:
    quality = report.get("answer_quality") or {}
    issues = quality.get("issues")
    if isinstance(issues, list):
        return [str(item) for item in issues if str(item)]
    reason = quality.get("reason") or report.get("error") or ""
    return [str(reason)] if reason else []


def _evidence_paths(report: dict) -> list[str]:
    paths = []
    if report.get("evidence_path"):
        paths.append(report["evidence_path"])
    raw = report.get("raw") or {}
    for item in raw.get("evidence", []) or []:
        if item not in paths:
            paths.append(item)
    return paths


def _artifact_paths(report: dict) -> dict:
    evidence = _evidence_paths(report)
    primary = evidence[0] if evidence else ""
    return {
        "evidence_path": primary,
        "screenshot_path": f"{primary}/screenshot.png" if primary else "",
        "metadata_path": f"{primary}/metadata.json" if primary else "",
    }


def _provider_matrix_row(provider: str) -> dict:
    report = _load_report(provider)
    state = state_from_report(provider, report)
    if state == ProviderState.NOT_CONFIGURED:
        state = profile_state(provider)
    quality = report.get("answer_quality") or {}
    artifacts = _artifact_paths(report)
    return {
        "provider": provider,
        "state": state.value,
        "status": (quality.get("quality") or report.get("retry_status") or state.value),
        "login": bool(report.get("login_detection")),
        "send": bool(report.get("send_prompt")),
        "wait": bool(report.get("wait_complete")),
        "extract": bool(report.get("extract_answer")),
        "aq": quality.get("quality") or "NOT_RUN",
        "last_tested": report.get("created_at", ""),
        "success": bool(report.get("success")),
        "failure_reason": report.get("failure_stage") or report.get("error") or "; ".join(_quality_issues(report)),
        "used_selector": report.get("used_selector", ""),
        "quality_issues": _quality_issues(report),
        "fallback_result": report.get("fallback_result"),
        **artifacts,
    }


@router.get("/web-ai/profiles/status")
async def get_profile_status():
    status = _load_status()
    result = {}
    for provider in PROVIDERS:
        profile_dir = _profile_dir() / provider
        provider_status = status.get(provider, {})
        has_profile = profile_dir.exists() and any(profile_dir.iterdir())
        test_path = _test_report_path(provider)
        test_status = "NOT_CONFIGURED"
        test_summary = None
        if test_path.exists():
            try:
                test_data = json.loads(test_path.read_text(encoding="utf-8"))
                test_status = (
                    "PASS"
                    if test_data.get("success")
                    else (
                        "PARTIAL"
                        if test_data.get("login_detection")
                        or test_data.get("send_prompt")
                        else "FAIL"
                    )
                )
                test_summary = {
                    "success": test_data.get("success"),
                    "login_detection": test_data.get("login_detection"),
                    "send_prompt": test_data.get("send_prompt"),
                    "wait_complete": test_data.get("wait_complete"),
                    "answer_quality": test_data.get("answer_quality", {}),
                    "created_at": test_data.get("created_at"),
                }
            except Exception:
                test_status = "error"
        result[provider] = {
            "provider": provider,
            "initialized": bool(provider_status),
            "logged_in": provider_status.get("logged_in", False),
            "has_profile_dir": has_profile,
            "test_status": test_status,
            "test_summary": test_summary,
            "recommendation_label": _recommendation(provider, test_status),
            "last_initialized": provider_status.get("initialized_at"),
            "workspace_state": (
                workspace_manager.last_statuses.get(provider).state.value
                if workspace_manager.last_statuses.get(provider)
                else profile_state(provider).value
            ),
        }
    return {"profiles": result}


@router.get("/web-ai/test-matrix")
async def get_web_ai_test_matrix():
    return {
        "providers": [_provider_matrix_row(provider) for provider in PROVIDERS],
        "report_dir": str(_test_report_dir()),
    }


@router.post("/web-ai/profiles/{provider}/init")
async def init_profile(provider: str):
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    existing = _load_status()
    return {
        "provider": provider,
        "needs_manual_login": True,
        "instructions": f"Run: PYTHONPATH=. python scripts/init_web_ai_profile.py --provider {provider}",
        "current_status": existing.get(provider, {}),
    }


@router.post("/web-ai/profiles/{provider}/test")
async def test_profile(provider: str):
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}
    test_path = _test_report_path(provider)
    if test_path.exists():
        data = json.loads(test_path.read_text(encoding="utf-8"))
        return {"provider": provider, "result": data}
    return {
        "provider": provider,
        "needs_test_run": True,
        "command": f"PYTHONPATH=. python scripts/test_web_ai_{provider}.py",
    }


@router.post("/web-ai/profiles/{provider}/reset")
async def reset_profile(provider: str, payload: dict = Body(default_factory=dict)):
    """Delete persistent profile and test reports for a provider."""
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}
    import shutil

    profile_dir = _profile_dir() / provider
    test_path = _test_report_path(provider)
    if not payload.get("confirm"):
        return {
            "provider": provider,
            "confirmation_required": True,
            "will_delete": {
                "profile_dir": str(profile_dir),
                "test_report": str(test_path),
            },
            "will_preserve": ["settings.json", "evidence", "tasks", "other provider profiles"],
        }

    results = {}
    await workspace_manager.close_workspace(provider)
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
        results["profile_deleted"] = True
    if test_path.exists():
        test_path.unlink()
        results["test_report_deleted"] = True
    # Also remove from profile_status
    status = _load_status()
    if provider in status:
        del status[provider]
        status_path = _status_path()
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        results["status_cleared"] = True
    return {"provider": provider, "results": results}


@router.post("/web-ai/workspace/{provider}/open")
async def open_workspace(provider: str, payload: dict = Body(default_factory=dict)):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    request_id = str(payload.get("request_id") or uuid.uuid4().hex)
    workspace_manager.open_request_ids[provider] = request_id
    current = await workspace_manager.get_workspace_status(provider)
    if current.state in {ProviderState.OPENING, ProviderState.READY, ProviderState.BUSY}:
        current.request_id = request_id
        return current.to_dict()
    browser_status = playwright_status_payload()
    if not browser_status.get("chromium_found"):
        return {
            **current.to_dict(),
            "request_id": request_id,
            "workspace_state": current.state.value,
            "browser_started": False,
            "page_created": False,
            "visible_window_expected": True,
            "profile_dir": str(_profile_dir() / provider),
            "current_url": "",
            "failure_code": "PROJECT_BROWSER_MISSING",
            "failure_reason": "项目专用浏览器未找到，请先安装或配置项目专用 Chromium。",
            "playwright_status": browser_status,
        }
    try:
        await workspace_manager.open_workspace(provider)
    except Exception as exc:
        status = await workspace_manager.get_workspace_status(provider)
        data = status.to_dict()
        data.update(
            {
                "request_id": request_id,
                "workspace_state": status.state.value,
                "failure_reason": str(exc),
                "visible_window_expected": True,
            }
        )
        return data
    status = await workspace_manager.get_workspace_status(provider)
    status.request_id = request_id
    return status.to_dict()


@router.post("/external-ai/workspaces/{provider}/ask")
async def ask_workspace(provider: str, payload: dict = Body(default_factory=dict)):
    """Ask through the backend-owned persistent workspace.

    Local UI and E2E clients use this endpoint so they never open the provider
    profile from a second process.
    """
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        return {"success": False, "failure_reason": "prompt_required"}
    result = await WebAISkill().execute(
        prompt,
        {
            "task_id": payload.get("task_id") or "external_ai_workspace_api",
            "step_id": payload.get("step_id") or "step_1",
            "provider": provider,
            "target": provider,
            "prompt": prompt,
            "purpose": payload.get("purpose") or "workspace_api",
            "wait_timeout": payload.get("wait_timeout", 180),
            "max_followups": 0,
            "reuse_workspace": True,
            "debug": bool(payload.get("debug", False)),
            "request_id": payload.get("request_id") or "",
        },
    )
    metadata = result.metadata or {}
    quality = metadata.get("quality_check") or {}
    status = await workspace_manager.get_workspace_status(provider)
    return {
        "success": result.success,
        "provider": provider,
        "workspace_reused": bool(metadata.get("workspace_reused")),
        "workspace_state": status.state.value,
        "profile_owner": metadata.get("profile_owner", "backend"),
        "second_context_created": bool(metadata.get("second_context_created", False)),
        "request_id": metadata.get("request_id", ""),
        "send_success": bool((metadata.get("send") or {}).get("send_success")),
        "extract_success": bool(result.result),
        "answer": result.result,
        "answer_quality": quality,
        "quality_issues": quality.get("issues")
        or ([quality.get("reason")] if quality.get("reason") else []),
        "used_selector": metadata.get("used_selector", ""),
        "evidence_saved": bool(result.evidence),
        "evidence_path": metadata.get("evidence_path", ""),
        "need_user_intervention": bool(metadata.get("need_user_intervention")),
        "failure_reason": metadata.get("failure_reason") or result.error or "",
        "workspace_status": status.to_dict(),
    }


@router.post("/web-ai/workspace/{provider}/close")
async def close_workspace(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    status = await workspace_manager.close_workspace(provider)
    return status.to_dict()


@router.get("/web-ai/workspace/{provider}/status")
async def workspace_status(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    status = await workspace_manager.get_workspace_status(provider)
    return status.to_dict()


@router.post("/web-ai/workspace/{provider}/resume")
async def resume_workspace(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    status = await workspace_manager.get_workspace_status(provider)
    can_resume = status.state.value in {"READY", "PASS", "PARTIAL"}
    suggested_user_action = (
        ""
        if can_resume
        else "请在工作区窗口完成登录/验证/页面处理，然后点击“我已处理，继续”。"
    )
    return {
        **status.to_dict(),
        "can_resume": can_resume,
        "pending_external_ai_action": not can_resume,
        "suggested_user_action": suggested_user_action,
    }


@router.post("/web-ai/workspace/{provider}/test")
async def test_workspace(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    status = await workspace_manager.get_workspace_status(provider)
    return {
        **status.to_dict(),
        "live_test_available": True,
        "live_test_requires_confirmation": True,
        "minimal_prompt_limit": 1,
        "message": "Live minimal is opt-in and sends no prompt until the user explicitly confirms.",
    }


@router.post("/web-ai/workspace/{provider}/live-minimal")
async def live_minimal_workspace(provider: str, payload: dict = Body(default_factory=dict)):
    """Run at most one explicit onboarding minimal prompt per provider."""
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    if payload.get("confirmed") is not True:
        return {
            "provider": provider,
            "success": False,
            "confirmation_required": True,
            "live_prompt_sent": False,
            "failure_reason": "user_confirmation_required",
        }
    existing = _load_report(provider)
    if existing.get("onboarding_live_minimal") and existing.get("success"):
        return {
            **existing,
            "reused_previous_result": True,
            "live_prompt_sent": False,
        }
    status = await workspace_manager.get_workspace_status(provider)
    if status.state not in {ProviderState.READY, ProviderState.PASS, ProviderState.PARTIAL}:
        return {
            **status.to_dict(),
            "provider": provider,
            "success": False,
            "need_user_intervention": True,
            "live_prompt_sent": False,
            "failure_reason": (
                "provider_login_or_user_action_required"
                if status.state in {ProviderState.NEED_LOGIN, ProviderState.NEED_USER_INTERVENTION}
                else f"provider_not_ready:{status.state.value}"
            ),
        }
    result = await WebAISkill().execute(
        "请只回复：连接正常",
        {
            "task_id": f"provider_onboarding_{provider}",
            "step_id": "minimal_live",
            "provider": provider,
            "target": provider,
            "purpose": "provider_onboarding_live_minimal",
            "max_followups": 0,
            "reuse_workspace": True,
            "debug": True,
        },
    )
    metadata = result.metadata or {}
    quality = metadata.get("quality_check") or {}
    accepted = bool(
        result.success and quality.get("quality") in {"PASS", "PASS_WITH_WARNING"}
    )
    report = {
        "provider": provider,
        "success": accepted,
        "onboarding_live_minimal": True,
        "created_at": datetime.now().isoformat(),
        "login_detection": True,
        "send_prompt": bool((metadata.get("send") or {}).get("send_success")),
        "wait_complete": bool(metadata.get("complete", True)),
        "extract_answer": bool(result.result),
        "answer_quality": quality,
        "evidence_saved": bool(result.evidence),
        "evidence_path": metadata.get("evidence_path", ""),
        "used_selector": metadata.get("used_selector", ""),
        "workspace_reused": bool(metadata.get("workspace_reused")),
        "second_context_created": bool(metadata.get("second_context_created", False)),
        "live_prompt_sent": True,
        "prompt_count": 1,
        "need_user_intervention": bool(metadata.get("need_user_intervention")),
        "failure_reason": metadata.get("failure_reason") or result.error or "",
    }
    path = _test_report_path(provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


@router.get("/web-ai/workspace/{provider}/evidence")
async def workspace_evidence(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    root = _paths().evidence_dir / "web_ai" / provider
    if not root.exists():
        return {"provider": provider, "evidence": []}
    items = sorted([p for p in root.iterdir() if p.is_dir()], reverse=True)[:10]
    return {
        "provider": provider,
        "evidence": [
            {
                "path": str(path),
                "metadata": str(path / "metadata.json"),
                "screenshot": str(path / "screenshot.png"),
            }
            for path in items
        ],
    }


@router.get("/web-ai/workspaces/console")
async def workspace_console():
    return await workspace_manager.workspace_console()
