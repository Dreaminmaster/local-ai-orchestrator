from backend.skills.base import Skill, SkillResult, RiskLevel
from .screen_observer import ScreenObserver
from .visual_locator import VisualLocator
from .action_executor import ActionExecutor
from .ocr_locator import OCRLocator
from .vision_backend import VisionModelBackend, UITARSBackend


class DesktopVisualSkill(Skill):
    name = "desktop_visual"
    description = (
        "Observe screen, locate UI targets, and execute visual desktop actions"
    )
    capabilities = [
        "observe_screen",
        "click_by_description",
        "type_text",
        "hotkey",
        "ocr_locate",
        "vision_locate",
        "ui_tars_reserved",
    ]
    risk_level = RiskLevel.MEDIUM

    def __init__(self, vision_backend=None):
        self.observer = ScreenObserver()
        self.ocr = OCRLocator()
        self.vision_backend = vision_backend or VisionModelBackend()
        self.ui_tars_backend = UITARSBackend()
        self.locator = VisualLocator(self.vision_backend)
        self.executor = ActionExecutor()

    async def can_handle(self, task: dict, state: dict) -> bool:
        desc = task.get("description", "").lower()
        return any(k in desc for k in ["screen", "click", "desktop", "ocr", "visual"])

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "observe_screen")
        obs = self.observer.observe(
            context.get("save_as", "runtime/evidence/screen.png")
        )
        if action == "observe_screen":
            return SkillResult(
                self.name,
                True,
                f"Observed screen {obs.width}x{obs.height}",
                evidence=[obs.screenshot_path],
                metadata=obs.__dict__,
            )
        if action == "ocr_locate":
            found = self.ocr.locate_text(
                obs.screenshot_path, context.get("text", instruction)
            )
            return SkillResult(
                self.name,
                bool(found),
                "OCR locate result",
                evidence=[obs.screenshot_path],
                metadata={"location": found},
            )
        if action == "vision_locate":
            found = self.vision_backend.locate(
                obs.screenshot_path, context.get("target", instruction)
            )
            return SkillResult(
                self.name,
                bool(found),
                "Vision locate result",
                evidence=[obs.screenshot_path],
                metadata={"location": found},
            )
        if action == "click_by_description":
            loc = self.locator.locate(
                obs, context.get("target", instruction), context.get("hints")
            )
            res = self.executor.click(loc["x"], loc["y"])
            after = self.observer.observe(
                context.get("after_save_as", "runtime/evidence/screen_after_click.png")
            )
            return SkillResult(
                self.name,
                True,
                f"Clicked target: {context.get('target', instruction)}",
                evidence=[obs.screenshot_path, after.screenshot_path],
                metadata={"location": loc, "action": res, "after": after.__dict__},
            )
        if action == "type_text":
            res = self.executor.type_text(context.get("text", instruction))
            after = self.observer.observe(
                context.get("after_save_as", "runtime/evidence/screen_after_type.png")
            )
            return SkillResult(
                self.name,
                True,
                "Typed text",
                evidence=[obs.screenshot_path, after.screenshot_path],
                metadata=res,
            )
        if action == "hotkey":
            return SkillResult(
                self.name,
                True,
                "Pressed hotkey",
                evidence=[obs.screenshot_path],
                metadata=self.executor.hotkey(context.get("keys", [])),
            )
        return SkillResult(
            self.name,
            False,
            "",
            error=f"Unknown action: {action}",
            evidence=[obs.screenshot_path],
        )
