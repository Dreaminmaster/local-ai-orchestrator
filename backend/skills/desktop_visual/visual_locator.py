class VisualLocator:
    """Locates UI elements. Current MVP uses simple coordinate hints and center fallback."""
    def locate(self, observation, description: str, hints: dict | None = None) -> dict:
        if hints and "x" in hints and "y" in hints:
            return {"x": int(hints["x"]), "y": int(hints["y"]), "confidence": 1.0, "method": "hint"}
        return {"x": observation.width // 2, "y": observation.height // 2, "confidence": 0.2, "method": "center_fallback", "description": description}
