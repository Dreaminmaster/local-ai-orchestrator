from .base import DesktopVisualBackend


class AccessibilityReservedBackend(DesktopVisualBackend):
    name = "accessibility_reserved"

    def locate(self, screenshot_path: str, target: str) -> dict | None:
        return None
