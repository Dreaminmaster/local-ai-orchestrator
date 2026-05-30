import importlib.util
import json
from pathlib import Path


class PluginLoader:
    def __init__(self, plugin_dir: str = "plugins/custom_skills"):
        self.plugin_dir = Path(plugin_dir)

    def discover(self) -> list[dict]:
        manifests = []
        for p in self.plugin_dir.glob("*/manifest.json"):
            manifests.append(json.loads(p.read_text(encoding="utf-8")))
        return manifests

    def load_skill(self, manifest: dict):
        path = self.plugin_dir / manifest["module"]
        spec = importlib.util.spec_from_file_location(manifest["name"], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, manifest["class_name"])()
