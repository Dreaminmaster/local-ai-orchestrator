from .base import DesktopVisualBackend


class UITARSReservedBackend(DesktopVisualBackend):
    name = "ui_tars_reserved"

    def locate(self, screenshot_path: str, target: str) -> dict | None:
        return None
