import os
import tempfile
import unittest
from pathlib import Path

from backend.api.playwright_status import _chromium_found, playwright_status_payload
from backend.runtime_paths import installed_app_data_dir, resolve_runtime_paths
from backend.settings_store import SettingsStore


class RuntimePathsSettingsPlaywrightTests(unittest.TestCase):
    def test_installed_app_data_locations(self):
        home = Path("/Users/alice")
        self.assertEqual(
            installed_app_data_dir(system="Darwin", home=home),
            Path("/Users/alice/Library/Application Support/Local AI Orchestrator"),
        )
        self.assertEqual(
            installed_app_data_dir(system="Linux", home=home),
            Path("/Users/alice/.local/share/local-ai-orchestrator"),
        )

    def test_dev_runtime_paths_are_project_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            paths = resolve_runtime_paths(project_root=root)
            self.assertEqual(paths.mode, "dev")
            self.assertEqual(paths.runtime_dir, root / "runtime")
            self.assertEqual(paths.playwright_browsers_path, root / ".playwright-browsers")
            paths.ensure()
            self.assertTrue(paths.browser_profiles_dir.exists())
            self.assertTrue(paths.test_reports_dir.exists())

    def test_settings_default_created_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = resolve_runtime_paths(project_root=Path(tmp).resolve())
            settings = SettingsStore(paths).load()
            self.assertTrue(paths.settings_path.exists())
            self.assertEqual(settings["lmstudio_endpoint"], "http://127.0.0.1:1234")
            self.assertEqual(
                settings["playwright_browsers_path"],
                str(paths.playwright_browsers_path),
            )

    def test_settings_rejects_plaintext_secret_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SettingsStore(resolve_runtime_paths(project_root=Path(tmp).resolve()))
            with self.assertRaises(ValueError):
                store.save({"api_key": "do-not-store"})

    def test_chromium_detection_and_status_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            browser_root = root / ".playwright-browsers"
            self.assertFalse(_chromium_found(browser_root))
            (browser_root / "chromium-1234" / "chrome-mac" / "Chromium.app").mkdir(parents=True)
            self.assertTrue(_chromium_found(browser_root))

            old_project = os.environ.get("PROJECT_ROOT")
            old_runtime = os.environ.get("LOCAL_AI_RUNTIME_DIR")
            old_playwright = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            os.environ["PROJECT_ROOT"] = str(root)
            os.environ["LOCAL_AI_RUNTIME_DIR"] = str(root / "runtime")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_root)
            try:
                payload = playwright_status_payload()
            finally:
                if old_project is None:
                    os.environ.pop("PROJECT_ROOT", None)
                else:
                    os.environ["PROJECT_ROOT"] = old_project
                if old_runtime is None:
                    os.environ.pop("LOCAL_AI_RUNTIME_DIR", None)
                else:
                    os.environ["LOCAL_AI_RUNTIME_DIR"] = old_runtime
                if old_playwright is None:
                    os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
                else:
                    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = old_playwright
            self.assertTrue(payload["exists"])
            self.assertTrue(payload["chromium_found"])
            self.assertEqual(payload["recommended_action"], "ready")


if __name__ == "__main__":
    unittest.main()
