"""Desktop Skill — Desktop automation via PyAutoGUI."""
from __future__ import annotations
import os
from .base import Skill, SkillResult, RiskLevel


class DesktopSkill(Skill):
    name = "desktop"
    description = "Control desktop: screenshots, mouse, keyboard, app launching"
    capabilities = [
        "screenshot", "click", "type_text", "hotkey",
        "open_app", "move_mouse", "get_screen_size",
    ]
    risk_level = RiskLevel.MEDIUM

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["desktop", "screenshot", "click", "mouse", "keyboard", "app", "window"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "screenshot")

        try:
            import pyautogui
            pyautogui.FAILSAFE = True
        except ImportError:
            return SkillResult(
                skill=self.name, success=False, result="",
                error="PyAutoGUI not installed. Run: pip install pyautogui",
            )

        try:
            if action == "screenshot":
                return await self._screenshot(context.get("save_as", "desktop_screenshot.png"))
            elif action == "click":
                x, y = context.get("x", 0), context.get("y", 0)
                return await self._click(x, y)
            elif action == "type_text":
                return await self._type_text(context.get("text", ""))
            elif action == "hotkey":
                keys = context.get("keys", [])
                return await self._hotkey(keys)
            elif action == "open_app":
                return await self._open_app(context.get("app_name", ""))
            elif action == "get_screen_size":
                return await self._get_screen_size()
            else:
                return SkillResult(
                    skill=self.name, success=False, result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(skill=self.name, success=False, result="", error=str(e))

    async def _screenshot(self, save_as: str) -> SkillResult:
        import pyautogui
        img = pyautogui.screenshot()
        img.save(save_as)
        return SkillResult(
            skill=self.name, success=True,
            result=f"Desktop screenshot saved: {save_as}",
            evidence=[save_as],
        )

    async def _click(self, x: int, y: int) -> SkillResult:
        import pyautogui
        pyautogui.click(x, y)
        return SkillResult(
            skill=self.name, success=True,
            result=f"Clicked at ({x}, {y})",
        )

    async def _type_text(self, text: str) -> SkillResult:
        import pyautogui
        pyautogui.typewrite(text, interval=0.02) if text.isascii() else pyautogui.write(text)
        return SkillResult(
            skill=self.name, success=True,
            result=f"Typed {len(text)} characters",
        )

    async def _hotkey(self, keys: list[str]) -> SkillResult:
        import pyautogui
        pyautogui.hotkey(*keys)
        return SkillResult(
            skill=self.name, success=True,
            result=f"Pressed hotkey: {'+'.join(keys)}",
        )

    async def _open_app(self, app_name: str) -> SkillResult:
        import subprocess, sys
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-a", app_name])
        elif sys.platform == "win32":
            subprocess.Popen(["start", app_name], shell=True)
        else:
            subprocess.Popen([app_name])
        return SkillResult(
            skill=self.name, success=True,
            result=f"Opened app: {app_name}",
        )

    async def _get_screen_size(self) -> SkillResult:
        import pyautogui
        w, h = pyautogui.size()
        return SkillResult(
            skill=self.name, success=True,
            result=f"Screen size: {w}x{h}",
            metadata={"width": w, "height": h},
        )
