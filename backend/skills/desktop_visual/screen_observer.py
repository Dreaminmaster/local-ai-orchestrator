from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ScreenObservation:
    screenshot_path: str
    width: int
    height: int
    timestamp: str


class ScreenObserver:
    def observe(self, save_as: str = "runtime/evidence/screen.png") -> ScreenObservation:
        import pyautogui
        Path(save_as).parent.mkdir(parents=True, exist_ok=True)
        img = pyautogui.screenshot()
        img.save(save_as)
        return ScreenObservation(save_as, img.width, img.height, datetime.now().isoformat())
