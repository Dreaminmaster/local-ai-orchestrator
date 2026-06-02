"""Web AI profile management API."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from backend.skills.external_ai_web.provider_status import (
    PROVIDERS,
    ProviderState,
    normalize_provider,
    profile_state,
    state_from_report,
)
from backend.skills.external_ai_web.workspace_manager import workspace_manager

router = APIRouter(tags=["web-ai-profiles"])

PROFILE_DIR = Path("runtime/browser_profiles")
STATUS_PATH = Path("runtime/test_reports/web_ai/profile_status.json")
TEST_REPORT_DIR = Path("runtime/test_reports/web_ai")


def _load_status():
    if STATUS_PATH.exists():
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    return {}


def _test_report_path(provider: str) -> Path:
    return TEST_REPORT_DIR / f"{provider}.json"


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
        "failure_reason": report.get("failure_stage")
        or report.get("error")
        or "; ".join(_quality_issues(report)),
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
        profile_dir = PROFILE_DIR / provider
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
        }
    return {"profiles": result}


@router.get("/web-ai/test-matrix")
async def get_web_ai_test_matrix():
    return {
        "providers": [_provider_matrix_row(provider) for provider in PROVIDERS],
        "report_dir": str(TEST_REPORT_DIR),
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
async def reset_profile(provider: str):
    """Delete persistent profile and test reports for a provider."""
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}
    import shutil

    profile_dir = PROFILE_DIR / provider
    test_path = _test_report_path(provider)

    results = {}
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
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(
            json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        results["status_cleared"] = True
    return {"provider": provider, "results": results}


@router.post("/web-ai/workspace/{provider}/open")
async def open_workspace(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    await workspace_manager.open_workspace(provider)
    status = await workspace_manager.get_workspace_status(provider)
    return status.to_dict()


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
    if provider == "claude":
        return {
            **status.to_dict(),
            "live_test_available": True,
            "live_test_command": "PYTHONPATH=. python scripts/e2e_claude_workspace_live.py",
            "message": "Live Claude Workspace E2E is opt-in and should be run only after user confirmation.",
        }
    return {
        **status.to_dict(),
        "live_test_available": False,
        "message": "Provider live test is not enabled in this phase.",
    }


@router.get("/web-ai/workspace/{provider}/evidence")
async def workspace_evidence(provider: str):
    provider = normalize_provider(provider)
    if provider not in PROVIDERS:
        return {"error": f"Unknown provider: {provider}", "providers": PROVIDERS}
    root = Path("runtime/evidence/web_ai") / provider
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
