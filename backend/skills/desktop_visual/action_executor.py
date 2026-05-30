class ActionExecutor:
    def click(self, x: int, y: int):
        import pyautogui
        pyautogui.click(x, y)
        return {"action": "click", "x": x, "y": y}

    def type_text(self, text: str):
        import pyautogui
        pyautogui.write(text)
        return {"action": "type_text", "length": len(text)}

    def hotkey(self, keys: list[str]):
        import pyautogui
        pyautogui.hotkey(*keys)
        return {"action": "hotkey", "keys": keys}
