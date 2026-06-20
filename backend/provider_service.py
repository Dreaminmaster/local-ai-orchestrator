"""Product-level provider configuration, detection, testing, and routing."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from backend.settings_store import SettingsStore
from backend.skills.external_ai_web.provider_status import (
    PROVIDERS,
    load_provider_report,
    profile_state,
    state_from_report,
)

LOCAL_PROVIDERS = ("lmstudio", "ollama")
WEB_PROVIDERS = tuple(PROVIDERS)
ROLE_NAMES = ("planner", "executor", "repair", "verifier", "summarizer")
WEB_CAPABILITIES = (
    "login",
    "send",
    "wait",
    "extract",
    "new_conversation",
    "session_persistence",
    "model_selection",
    "evidence",
    "pending_resume",
    "agent_joint_task",
)


def _request_json(url: str, *, method: str = "GET", payload: dict | None = None, timeout: float = 3) -> tuple[int, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else {}


class ProviderService:
    def __init__(self, settings: SettingsStore | None = None):
        self.store = settings or SettingsStore()

    def settings(self) -> dict:
        return self.store.load()

    def save_settings(self, patch: dict) -> dict:
        current = self.settings()
        merged = self._merge(current, patch)
        self.store.save(merged)
        return merged

    def configure(self, provider: str, payload: dict) -> dict:
        if provider in LOCAL_PROVIDERS:
            patch = {"local_models": {provider: payload}}
        elif provider in WEB_PROVIDERS:
            patch = {"external_ai": {"providers": {provider: payload}}}
        else:
            raise ValueError("unknown_provider")
        return self.save_settings(patch)

    def list_models(self, provider: str) -> dict:
        if provider not in LOCAL_PROVIDERS:
            return {"provider": provider, "models": [], "failure_reason": "web_provider_models_are_page_managed"}
        return self.detect_local(provider)

    def set_default_model(self, provider: str, model: str) -> dict:
        settings = self.configure(provider, {"default_model": model})
        return {"provider": provider, "default_model": model, "settings_path": str(self.store.path), "success": True}

    def onboarding(self) -> dict:
        overview = self.overview()
        all_providers = [*overview["local"], *overview["web"]]
        verified = sum(
            item.get("acceptance_status") == "VERIFIED" for item in all_providers
        )
        enabled = sum(bool(item.get("enabled")) for item in all_providers)
        return {
            "providers": all_providers,
            "enabled_count": enabled,
            "verified_count": verified,
            "default_local_provider": overview["local_model_routing"].get(
                "default_provider", "lmstudio"
            ),
            "default_external_provider": next(
                (
                    name
                    for name in overview["routing"].get("priority", [])
                    if overview["routing"]["providers"].get(name, {}).get("enabled")
                ),
                "",
            ),
            "routing": overview["routing"],
            "completed": bool(overview["routing"].get("onboarding_completed")),
        }

    def save_onboarding(self, choices: dict[str, str]) -> dict:
        local_patch: dict[str, dict] = {}
        web_patch: dict[str, dict] = {}
        for provider, choice in choices.items():
            if choice not in {"enabled", "skipped", "later"}:
                continue
            payload = {
                "enabled": choice == "enabled",
                "onboarding_choice": choice,
            }
            if provider in LOCAL_PROVIDERS:
                local_patch[provider] = payload
            elif provider in WEB_PROVIDERS:
                web_patch[provider] = payload
        self.save_settings(
            {
                "local_models": local_patch,
                "external_ai": {
                    "providers": web_patch,
                    "onboarding_completed": True,
                },
            }
        )
        return self.onboarding()

    def export_diagnostics(self, provider: str) -> dict:
        if provider in LOCAL_PROVIDERS:
            status = self.detect_local(provider)
        elif provider in WEB_PROVIDERS:
            status = self.web_status(provider)
        else:
            return {"provider": provider, "state": "ERROR", "failure_reason": "unknown_provider"}
        return {key: value for key, value in status.items() if key not in {"answer_preview"}}

    def detect_local(self, provider: str) -> dict:
        config = self.settings()["local_models"][provider]
        endpoint = str(config["endpoint"]).rstrip("/")
        started = time.monotonic()
        try:
            if provider == "lmstudio":
                status, body = _request_json(f"{endpoint}/v1/models", timeout=2)
                models = [item.get("id", "") for item in body.get("data", []) if item.get("id")]
                compatible = status == 200 and isinstance(body.get("data"), list)
            else:
                status, body = _request_json(f"{endpoint}/api/tags", timeout=2)
                models = [item.get("name", "") for item in body.get("models", []) if item.get("name")]
                compatible = status == 200 and isinstance(body.get("models"), list)
            state = "READY" if compatible and models else "NEED_MODEL" if compatible else "DEGRADED"
            error = ""
        except urllib.error.HTTPError as exc:
            status, models, compatible, state, error = exc.code, [], False, "ERROR", f"http_{exc.code}"
        except Exception as exc:
            status, models, compatible, state, error = 0, [], False, "NEED_LOCAL_SERVICE", type(exc).__name__
        return {
            "provider": provider,
            "kind": "local",
            "enabled": bool(config.get("enabled")),
            "state": "DISABLED" if not config.get("enabled") else state,
            "endpoint": endpoint,
            "models": models,
            "default_model": config.get("default_model") or "",
            "timeout_seconds": config.get("timeout_seconds", 120),
            "max_context": config.get("max_context", 32768),
            "temperature": config.get("temperature", 0.3),
            "max_tokens": config.get("max_tokens", 4096),
            "roles": config.get("roles", []),
            "openai_compatible": compatible if provider == "lmstudio" else False,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "status_code": status,
            "failure_reason": error,
            "acceptance_status": "VERIFIED" if state == "READY" else state,
            "onboarding_choice": config.get(
                "onboarding_choice", "enabled" if config.get("enabled") else "later"
            ),
            "routing_role": (
                "default"
                if provider == self.settings()["local_models"].get("default_provider")
                else "disabled"
                if not config.get("enabled")
                else "fallback"
            ),
        }

    def test_local_chat(self, provider: str, model: str = "") -> dict:
        detected = self.detect_local(provider)
        chosen = model or detected.get("default_model") or next(iter(detected.get("models") or []), "")
        if detected["state"] not in {"READY", "DEGRADED"}:
            return {**detected, "chat_success": False, "failure_reason": detected["failure_reason"] or "provider_disconnected"}
        if not chosen:
            return {**detected, "chat_success": False, "failure_reason": "model_not_loaded"}
        config = self.settings()["local_models"][provider]
        endpoint = str(config["endpoint"]).rstrip("/")
        timeout = min(float(config.get("timeout_seconds", 120)), 180)
        payload = {
            "model": chosen,
            "messages": [{"role": "user", "content": "请只回复：连接正常"}],
            "stream": False,
        }
        if provider == "lmstudio":
            payload.update(temperature=0, max_tokens=32)
            url = f"{endpoint}/v1/chat/completions"
        else:
            payload["options"] = {"temperature": 0, "num_predict": 32}
            url = f"{endpoint}/api/chat"
        try:
            status, body = _request_json(url, method="POST", payload=payload, timeout=timeout)
            answer = (
                body.get("choices", [{}])[0].get("message", {}).get("content", "")
                if provider == "lmstudio"
                else body.get("message", {}).get("content", "")
            )
            return {**detected, "model": chosen, "chat_success": bool(status == 200 and answer.strip()), "answer_preview": answer[:160], "failure_reason": "" if answer.strip() else "empty_response"}
        except urllib.error.HTTPError as exc:
            return {**detected, "model": chosen, "chat_success": False, "failure_reason": f"http_{exc.code}"}
        except Exception as exc:
            return {**detected, "model": chosen, "chat_success": False, "failure_reason": type(exc).__name__}

    def test_local_roles(self, provider: str) -> dict:
        settings = self.settings()["local_models"]
        results = {}
        for role in ROLE_NAMES:
            configured = str((settings.get("roles") or {}).get(role) or "")
            role_provider, _, role_model = configured.partition(":")
            selected_provider = role_provider if role_model else provider
            selected_model = role_model or str(settings.get(selected_provider, {}).get("default_model") or "")
            if selected_provider != provider:
                results[role] = {
                    "success": False,
                    "provider": selected_provider,
                    "model": selected_model,
                    "failure_reason": "role_uses_different_provider",
                }
                continue
            tested = self.test_local_chat(provider, selected_model)
            results[role] = {
                "success": bool(tested.get("chat_success")),
                "provider": provider,
                "model": tested.get("model", selected_model),
                "failure_reason": tested.get("failure_reason", ""),
            }
        return {
            "provider": provider,
            "roles": results,
            "success": all(item["success"] for item in results.values()),
        }

    def web_status(self, provider: str) -> dict:
        settings = self.settings()["external_ai"]
        config = settings["providers"][provider]
        report = load_provider_report(provider)
        state = state_from_report(provider, report).value if report else profile_state(provider).value
        if not config.get("enabled"):
            state = "DISABLED"
        quality = report.get("answer_quality") or {}
        capability = {
            "login": bool(report.get("login_detection")),
            "send": bool(report.get("send_prompt")),
            "wait": bool(report.get("wait_complete")),
            "extract": bool(report.get("extract_answer")),
            "new_conversation": bool(report.get("login_detection")),
            "session_persistence": bool(profile_state(provider).value != "NOT_CONFIGURED"),
            "model_selection": "NOT_VERIFIED",
            "evidence": bool(report.get("evidence_saved")),
            "pending_resume": True,
            "agent_joint_task": bool(report.get("agent_joint_task") or report.get("report_contains_claude_web")),
        }
        return {
            "provider": provider,
            "kind": "web",
            "enabled": bool(config.get("enabled")),
            "state": state,
            "default_model": config.get("default_model", ""),
            "last_tested": report.get("created_at", ""),
            "last_result": quality.get("quality") or ("PASS" if report.get("success") else ""),
            "needs_login": state == "NEED_LOGIN",
            "evidence_saved": bool(report.get("evidence_saved")),
            "capabilities": capability,
            "acceptance_status": (
                "VERIFIED"
                if state == "PASS"
                else "NEED_LOGIN"
                if state in {"NEED_LOGIN", "NOT_CONFIGURED"}
                else "DISABLED_BY_USER"
                if state == "DISABLED"
                else state
            ),
            "onboarding_choice": config.get(
                "onboarding_choice", "enabled" if config.get("enabled") else "later"
            ),
            "routing_role": config.get(
                "routing_role", "disabled" if not config.get("enabled") else "fallback"
            ),
            "route_eligible": bool(
                config.get("enabled")
                and state == "PASS"
                and config.get("onboarding_choice", "enabled") == "enabled"
            ),
        }

    def overview(self) -> dict:
        settings = self.settings()
        return {
            "local": [self.detect_local(provider) for provider in LOCAL_PROVIDERS],
            "web": [self.web_status(provider) for provider in WEB_PROVIDERS],
            "routing": settings["external_ai"],
            "local_model_routing": settings["local_models"],
            "settings_path": str(self.store.path),
        }

    def route(
        self,
        *,
        allow_external: bool = True,
        external_calls: int = 0,
        user_confirmed: bool = False,
    ) -> dict:
        settings = self.settings()
        local = [self.detect_local(provider) for provider in LOCAL_PROVIDERS]
        external = settings["external_ai"]
        policy = external["routing_policy"]
        ready_local = next(
            (
                provider
                for provider in local
                if provider["enabled"] and provider["state"] == "READY" and provider["models"]
            ),
            None,
        )
        if policy != "best_capability" and ready_local:
            return {
                "selected_provider": ready_local["provider"],
                "kind": "local",
                "reason": "enabled_ready_local_provider",
            }
        if policy == "fully_local" or not allow_external:
            return {"selected_provider": "rule_fallback", "kind": "rule", "reason": "external_ai_disabled_or_fully_local"}
        if external_calls >= int(external.get("max_calls_per_task", 1)):
            return {"selected_provider": "rule_fallback", "kind": "rule", "reason": "external_ai_call_limit_reached"}
        if policy == "manual_confirmation" and not user_confirmed:
            return {
                "selected_provider": "manual_confirmation",
                "kind": "manual",
                "reason": "external_ai_requires_user_confirmation",
            }
        if not external.get("allow_automatic") and not user_confirmed:
            return {
                "selected_provider": "manual_confirmation",
                "kind": "manual",
                "reason": "external_ai_requires_user_confirmation",
            }
        for name in external["priority"]:
            provider = self.web_status(name)
            if provider.get(
                "route_eligible",
                bool(provider.get("enabled") and provider.get("state") == "PASS"),
            ):
                return {"selected_provider": name, "kind": "web", "reason": "configured_tested_priority_provider", "confirmation_required": external["require_confirmation"]}
        if ready_local:
            return {
                "selected_provider": ready_local["provider"],
                "kind": "local",
                "reason": "no_verified_web_provider_using_ready_local",
            }
        return {"selected_provider": "rule_fallback", "kind": "rule", "reason": "no_configured_ready_provider"}

    @staticmethod
    def _merge(current: dict, patch: dict) -> dict:
        output = dict(current)
        for key, value in patch.items():
            output[key] = ProviderService._merge(output.get(key, {}), value) if isinstance(value, dict) and isinstance(output.get(key), dict) else value
        return output
