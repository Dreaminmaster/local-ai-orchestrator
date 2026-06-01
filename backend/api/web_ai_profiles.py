"""Web AI profile management API."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["web-ai-profiles"])

PROVIDERS = ["chatgpt", "claude", "doubao", "gemini", "kimi"]
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


@router.get("/web-ai/profiles/status")
async def get_profile_status():
    status = _load_status()
    result = {}
    for provider in PROVIDERS:
        profile_dir = PROFILE_DIR / provider
        provider_status = status.get(provider, {})
        has_profile = profile_dir.exists() and any(profile_dir.iterdir())
        test_path = _test_report_path(provider)
        test_status = "not_run"
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
