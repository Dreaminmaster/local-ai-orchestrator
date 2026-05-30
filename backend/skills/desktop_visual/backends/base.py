from abc import ABC, abstractmethod


class DesktopVisualBackend(ABC):
    name = "base"

    @abstractmethod
    def locate(self, screenshot_path: str, target: str) -> dict | None: ...
