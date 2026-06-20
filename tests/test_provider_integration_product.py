import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api.playwright_status import install_playwright_browser
from backend.provider_service import ProviderService
from backend.runtime_paths import resolve_runtime_paths
from backend.settings_store import SettingsStore
from backend.skills.external_ai_web.doubao_web_adapter import DoubaoWebAdapter
from backend.skills.external_ai_web.gemini_web_adapter import GeminiWebAdapter
from backend.skills.external_ai_web.kimi_web_adapter import KimiWebAdapter
from backend.skills.external_ai_web.provider_status import normalize_provider, state_from_report


class ProviderIntegrationProductTests(unittest.TestCase):
    def service(self, root: Path) -> ProviderService:
        return ProviderService(SettingsStore(resolve_runtime_paths(project_root=root)))

    def test_settings_cover_local_roles_and_all_web_providers(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.service(Path(tmp)).settings()
            self.assertEqual(
                set(settings["local_models"]["roles"]),
                {"planner", "executor", "repair", "verifier", "summarizer"},
            )
            self.assertEqual(
                set(settings["external_ai"]["providers"]),
                {"claude", "chatgpt", "gemini", "kimi", "doubao"},
            )
            self.assertEqual(
                settings["external_ai"]["providers"]["claude"]["onboarding_choice"],
                "enabled",
            )

    def test_web_aliases_and_pass_with_warning(self):
        self.assertEqual(normalize_provider("Gemini Web"), "gemini")
        self.assertEqual(normalize_provider("豆包 Web"), "doubao")
        state = state_from_report(
            "claude",
            {"success": True, "answer_quality": {"quality": "PASS_WITH_WARNING"}},
        )
        self.assertEqual(state.value, "PASS")

    def test_all_non_claude_adapters_follow_shared_constructor(self):
        for adapter in (GeminiWebAdapter, KimiWebAdapter, DoubaoWebAdapter):
            instance = adapter(page=object(), debug=True)
            self.assertTrue(instance.debug)

    def test_router_does_not_choose_disabled_or_unverified_web_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self.service(Path(tmp))
            service.save_settings(
                {
                    "local_models": {
                        "lmstudio": {"enabled": False},
                        "ollama": {"enabled": False},
                    },
                    "external_ai": {
                        "allow_automatic": True,
                        "providers": {
                            "claude": {"enabled": False},
                            "chatgpt": {"enabled": True},
                        },
                    },
                }
            )
            with patch.object(service, "web_status") as status:
                status.return_value = {"enabled": True, "state": "NOT_CONFIGURED"}
                decision = service.route()
            self.assertEqual(decision["selected_provider"], "rule_fallback")

    def test_onboarding_saves_all_choices_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self.service(Path(tmp))
            result = service.save_onboarding(
                {
                    "lmstudio": "enabled",
                    "ollama": "skipped",
                    "claude": "enabled",
                    "chatgpt": "enabled",
                    "gemini": "enabled",
                    "kimi": "enabled",
                    "doubao": "enabled",
                }
            )
            settings = service.settings()
            self.assertFalse(settings["local_models"]["ollama"]["enabled"])
            self.assertEqual(
                settings["local_models"]["ollama"]["onboarding_choice"], "skipped"
            )
            self.assertTrue(settings["external_ai"]["providers"]["gemini"]["enabled"])
            self.assertTrue(result["completed"])

    def test_only_verified_web_provider_is_route_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self.service(Path(tmp))
            service.save_settings(
                {
                    "local_models": {
                        "lmstudio": {"enabled": False},
                        "ollama": {"enabled": False},
                    },
                    "external_ai": {
                        "allow_automatic": True,
                        "providers": {"claude": {"enabled": True}},
                    },
                }
            )
            with patch.object(
                service,
                "web_status",
                return_value={"enabled": True, "state": "PARTIAL", "route_eligible": False},
            ):
                decision = service.route(user_confirmed=True)
            self.assertEqual(decision["selected_provider"], "rule_fallback")

    def test_routing_modes_and_call_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self.service(Path(tmp))
            service.save_settings(
                {
                    "local_models": {
                        "lmstudio": {"enabled": False},
                        "ollama": {"enabled": False},
                    },
                    "external_ai": {
                        "routing_policy": "manual_confirmation",
                        "allow_automatic": True,
                        "max_calls_per_task": 1,
                        "providers": {"claude": {"enabled": True}},
                    },
                }
            )
            with patch.object(
                service,
                "web_status",
                return_value={"enabled": True, "state": "PASS"},
            ):
                manual = service.route()
                confirmed = service.route(user_confirmed=True)
                limited = service.route(user_confirmed=True, external_calls=1)
            self.assertEqual(manual["kind"], "manual")
            self.assertEqual(confirmed["selected_provider"], "claude")
            self.assertEqual(limited["reason"], "external_ai_call_limit_reached")

    def test_playwright_install_requires_explicit_confirmation(self):
        preview = asyncio.run(install_playwright_browser({"confirm": False}))
        self.assertTrue(preview["confirmation_required"])
        self.assertFalse(preview["system_cache_used"])

    def test_settings_reject_secret_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self.service(Path(tmp))
            with self.assertRaises(ValueError):
                service.save_settings({"external_ai": {"api_key": "secret"}})


if __name__ == "__main__":
    unittest.main()
