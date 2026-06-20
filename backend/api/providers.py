"""Product provider management API."""

from __future__ import annotations

from fastapi import APIRouter, Body

from backend.provider_service import LOCAL_PROVIDERS, WEB_PROVIDERS, ProviderService

router = APIRouter(tags=["providers"])


@router.get("/providers")
async def provider_overview():
    return ProviderService().overview()


@router.get("/providers/onboarding")
async def provider_onboarding():
    return ProviderService().onboarding()


@router.post("/providers/onboarding")
async def save_provider_onboarding(payload: dict = Body(default_factory=dict)):
    return ProviderService().save_onboarding(payload.get("choices") or {})


@router.get("/providers/{provider}/detect")
async def detect_provider(provider: str):
    if provider in LOCAL_PROVIDERS:
        return ProviderService().detect_local(provider)
    if provider in WEB_PROVIDERS:
        return ProviderService().web_status(provider)
    return {"state": "ERROR", "failure_reason": "unknown_provider"}


@router.get("/providers/{provider}/models")
async def list_provider_models(provider: str):
    return ProviderService().list_models(provider)


@router.post("/providers/{provider}/default-model")
async def set_provider_default_model(provider: str, payload: dict = Body(default_factory=dict)):
    return ProviderService().set_default_model(provider, str(payload.get("model") or ""))


@router.get("/providers/{provider}/diagnostics")
async def provider_diagnostics(provider: str):
    return ProviderService().export_diagnostics(provider)


@router.post("/providers/{provider}/configure")
async def configure_provider(provider: str, payload: dict = Body(default_factory=dict)):
    if provider in LOCAL_PROVIDERS:
        patch = {"local_models": {provider: payload}}
    elif provider in WEB_PROVIDERS:
        patch = {"external_ai": {"providers": {provider: payload}}}
    else:
        return {"state": "ERROR", "failure_reason": "unknown_provider"}
    settings = ProviderService().save_settings(patch)
    return {"success": True, "provider": provider, "settings": settings}


@router.post("/providers/{provider}/test")
async def test_provider(provider: str, payload: dict = Body(default_factory=dict)):
    if provider in LOCAL_PROVIDERS:
        return ProviderService().test_local_chat(provider, str(payload.get("model") or ""))
    if provider in WEB_PROVIDERS:
        return {
            **ProviderService().web_status(provider),
            "live_prompt_sent": False,
            "suggested_user_action": "打开项目专用工作区并手动登录；live minimal 必须由用户明确触发。",
        }
    return {"state": "ERROR", "failure_reason": "unknown_provider"}


@router.post("/providers/{provider}/role-test")
async def test_provider_roles(provider: str):
    if provider not in LOCAL_PROVIDERS:
        return {"state": "ERROR", "failure_reason": "local_provider_required"}
    return ProviderService().test_local_roles(provider)


@router.post("/providers/routing")
async def save_routing(payload: dict = Body(default_factory=dict)):
    settings = ProviderService().save_settings({"external_ai": payload})
    return {"success": True, "routing": settings["external_ai"]}


@router.post("/providers/local-model-routing")
async def save_local_model_routing(payload: dict = Body(default_factory=dict)):
    settings = ProviderService().save_settings({"local_models": payload})
    return {"success": True, "local_models": settings["local_models"]}


@router.get("/providers/routing/decision")
async def routing_decision(
    allow_external: bool = True,
    external_calls: int = 0,
    user_confirmed: bool = False,
):
    return ProviderService().route(
        allow_external=allow_external,
        external_calls=external_calls,
        user_confirmed=user_confirmed,
    )
