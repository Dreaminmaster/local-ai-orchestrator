from .base import DesktopVisualBackend


class OCRBackend(DesktopVisualBackend):
    name = "ocr"

    def locate(self, screenshot_path: str, target: str) -> dict | None:
        return None
