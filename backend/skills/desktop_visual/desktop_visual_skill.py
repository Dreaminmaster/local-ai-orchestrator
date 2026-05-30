from backend.skills.base import Skill, SkillResult, RiskLevel
from .screen_observer import ScreenObserver
from .visual_locator import VisualLocator
from .action_executor import ActionExecutor


class DesktopVisualSkill(Skill):
    name = "desktop_visual"
    description = "Observe screen, locate UI targets, and execute visual desktop actions"
    capabilities = ["observe_screen", "click_by_description", "type_text", "hotkey"]
    risk_level = RiskLevel.MEDIUM

    def __init__(self):
        self.observer = ScreenObserver(); self.locator = VisualLocator(); self.executor = ActionExecutor()

    async def can_handle(self, task: dict, state: dict) -> bool:
        return "screen" in task.get("description", "").lower() or "click" in task.get("description", "").lower()

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "observe_screen")
        obs = self.observer.observe(context.get("save_as", "runtime/evidence/screen.png"))
        if action == "observe_screen":
            return SkillResult(self.name, True, f"Observed screen {obs.width}x{obs.height}", evidence=[obs.screenshot_path], metadata=obs.__dict__)
        if action == "click_by_description":
            loc = self.locator.locate(obs, context.get("target", instruction), context.get("hints"))
            res = self.executor.click(loc["x"], loc["y"])
            return SkillResult(self.name, True, f"Clicked target: {context.get('target', instruction)}", evidence=[obs.screenshot_path], metadata={"location": loc, "action": res})
        if action == "type_text":
            return SkillResult(self.name, True, "Typed text", evidence=[obs.screenshot_path], metadata=self.executor.type_text(context.get("text", instruction)))
        return SkillResult(self.name, False, "", error=f"Unknown action: {action}", evidence=[obs.screenshot_path])
