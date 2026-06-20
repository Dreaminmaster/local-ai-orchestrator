import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.core.agent import create_llm_provider
from backend.llm.lmstudio import LMStudioProvider
from backend.llm.ollama import OllamaProvider
from backend.runtime_paths import resolve_runtime_paths
from backend.settings_store import SettingsStore


class LocalModelProductRoutingTests(unittest.TestCase):
    def test_agent_uses_product_role_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = resolve_runtime_paths(project_root=root)
            store = SettingsStore(paths)
            settings = store.load()
            settings["local_models"]["ollama"].update(
                enabled=True,
                endpoint="http://127.0.0.1:11434",
                default_model="qwen-test",
            )
            settings["local_models"]["roles"]["repair"] = "ollama:qwen-test"
            store.save(settings)
            with patch.dict(
                os.environ,
                {
                    "PROJECT_ROOT": str(root),
                },
                clear=False,
            ):
                provider = create_llm_provider("repair")
            self.assertIsInstance(provider, OllamaProvider)
            self.assertEqual(provider.model, "qwen-test")

    def test_agent_uses_lmstudio_default_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = resolve_runtime_paths(project_root=root)
            store = SettingsStore(paths)
            settings = store.load()
            settings["local_models"]["lmstudio"]["default_model"] = "local-test"
            store.save(settings)
            with patch.dict(
                os.environ,
                {
                    "PROJECT_ROOT": str(root),
                },
                clear=False,
            ):
                provider = create_llm_provider("planner")
            self.assertIsInstance(provider, LMStudioProvider)
            self.assertEqual(provider.model, "local-test")


if __name__ == "__main__":
    unittest.main()
