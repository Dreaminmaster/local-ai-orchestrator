import json
from .base import DesktopVisualBackend


class VisionJSONBackend(DesktopVisualBackend):
    name = "vision_json"

    def __init__(self, json_path: str | None = None):
        self.json_path = json_path

    def locate(self, screenshot_path: str, target: str) -> dict | None:
        if not self.json_path:
            return None
        try:
            data = json.load(open(self.json_path, encoding="utf-8"))
            return data.get(target)
        except Exception:
            return None
