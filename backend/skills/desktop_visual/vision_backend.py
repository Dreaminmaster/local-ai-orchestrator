class VisionModelBackend:
    """Vision model locator interface.

    Production adapters can call GPT-4o Vision, Gemini, local vision models, or UI-TARS.
    """
    def locate(self, screenshot_path: str, description: str) -> dict | None:
        return None

class UITARSBackend(VisionModelBackend):
    """Reserved UI-TARS backend."""
    pass
