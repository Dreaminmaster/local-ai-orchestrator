import json
import asyncio
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.api.app_data import (
    app_data_status_payload,
    clear_safe_cache,
    export_diagnostics,
)
from backend.runtime_paths import resolve_runtime_paths
from backend.settings_store import SettingsStore
from backend.api.web_ai_profiles import reset_profile


class AppDataDiagnosticsTests(unittest.TestCase):
    def test_status_reports_writable_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            paths = resolve_runtime_paths(
                project_root=root,
                runtime_dir=root / "runtime",
                playwright_browsers_path=root / "playwright-browsers",
            ).ensure()
            payload = app_data_status_payload(paths)
            self.assertTrue(payload["exists"])
            self.assertTrue(payload["writable"])
            self.assertEqual(payload["app_data_dir"], str(root))

    def test_diagnostics_excludes_profiles_evidence_and_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            paths = resolve_runtime_paths(
                project_root=root,
                runtime_dir=root / "runtime",
                playwright_browsers_path=root / "playwright-browsers",
            ).ensure()
            SettingsStore(paths).load()
            (paths.logs_dir / "desktop-main.log").write_text("app_start\n", encoding="utf-8")
            (paths.browser_profiles_dir / "claude").mkdir(parents=True)
            (paths.browser_profiles_dir / "claude" / "Cookies").write_text("secret", encoding="utf-8")
            (paths.evidence_dir / "answer.txt").write_text("private answer", encoding="utf-8")
            (paths.runtime_dir / "orchestrator.db").write_bytes(b"database")

            output = export_diagnostics(paths)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("health.json", names)
                self.assertIn("settings.redacted.json", names)
                self.assertIn("logs/desktop-main.log", names)
                self.assertFalse(any("browser_profiles" in name for name in names))
                self.assertFalse(any("evidence" in name for name in names))
                self.assertFalse(any(name.endswith(".db") for name in names))

    def test_clear_cache_preserves_user_owned_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            paths = resolve_runtime_paths(
                project_root=root,
                runtime_dir=root / "runtime",
                playwright_browsers_path=root / "playwright-browsers",
            ).ensure()
            SettingsStore(paths).load()
            protected = [
                paths.settings_path,
                paths.browser_profiles_dir / "claude" / "Cookies",
                paths.evidence_dir / "answer.txt",
                paths.tasks_dir / "task.json",
            ]
            for path in protected:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("keep", encoding="utf-8")
            cache_files = [
                paths.runtime_dir / "tmp" / "temp.txt",
                paths.test_reports_dir / "report.json",
                paths.runtime_dir / "pip_cache" / "wheel.bin",
            ]
            for path in cache_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("remove", encoding="utf-8")

            result = clear_safe_cache(paths)

            self.assertTrue(all(path.exists() for path in protected))
            self.assertTrue(all(not path.exists() for path in cache_files))
            self.assertEqual(result["removed"]["tmp"], 1)
            self.assertEqual(result["removed"]["test_reports"], 1)
            self.assertEqual(result["removed"]["pip_cache"], 1)

    def test_redacted_settings_remain_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            paths = resolve_runtime_paths(
                project_root=root,
                runtime_dir=root / "runtime",
                playwright_browsers_path=root / "playwright-browsers",
            ).ensure()
            SettingsStore(paths).load()
            output = export_diagnostics(paths)
            with zipfile.ZipFile(output) as archive:
                data = json.loads(archive.read("settings.redacted.json"))
            self.assertIn("lmstudio_endpoint", data)

    def test_provider_reset_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            old_project = os.environ.get("PROJECT_ROOT")
            old_runtime = os.environ.get("LOCAL_AI_RUNTIME_DIR")
            os.environ["PROJECT_ROOT"] = str(root)
            os.environ["LOCAL_AI_RUNTIME_DIR"] = str(root / "runtime")
            try:
                profile = root / "runtime/browser_profiles/claude"
                profile.mkdir(parents=True)
                (profile / "Cookies").write_text("keep until confirmed", encoding="utf-8")
                preview = asyncio.run(reset_profile("claude", {}))
                self.assertTrue(preview["confirmation_required"])
                self.assertTrue(profile.exists())
            finally:
                if old_project is None:
                    os.environ.pop("PROJECT_ROOT", None)
                else:
                    os.environ["PROJECT_ROOT"] = old_project
                if old_runtime is None:
                    os.environ.pop("LOCAL_AI_RUNTIME_DIR", None)
                else:
                    os.environ["LOCAL_AI_RUNTIME_DIR"] = old_runtime


if __name__ == "__main__":
    unittest.main()
