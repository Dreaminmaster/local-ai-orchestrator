class VisualLocator:
    """Locates UI elements.

    MVP behavior:
    - use explicit x/y hints when provided;
    - use optional vision_backend callback if configured;
    - otherwise fallback to screen center.
    """

    def __init__(self, vision_backend=None):
        self.vision_backend = vision_backend

    def locate(self, observation, description: str, hints: dict | None = None) -> dict:
        if hints and "x" in hints and "y" in hints:
            return {
                "x": int(hints["x"]),
                "y": int(hints["y"]),
                "confidence": 1.0,
                "method": "hint",
            }
        if self.vision_backend:
            try:
                located = self.vision_backend.locate(
                    observation.screenshot_path, description
                )
                if located:
                    located.setdefault("method", "vision_backend")
                    return located
            except Exception as exc:
                return {
                    "x": observation.width // 2,
                    "y": observation.height // 2,
                    "confidence": 0.1,
                    "method": "vision_backend_failed",
                    "error": str(exc),
                }
        return {
            "x": observation.width // 2,
            "y": observation.height // 2,
            "confidence": 0.2,
            "method": "center_fallback",
            "description": description,
        }
