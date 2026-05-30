from __future__ import annotations

from .base import DesktopVisualBackend


class OCRBackend(DesktopVisualBackend):
    """OCR backend using pytesseract when available.

    Returns center coordinates of the first OCR box containing target text.
    """

    name = "ocr"

    def locate(self, screenshot_path: str, target: str) -> dict | None:
        try:
            from PIL import Image
            import pytesseract
        except Exception:
            return None

        try:
            image = Image.open(screenshot_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            target_lower = target.lower()
            for i, text in enumerate(data.get("text", [])):
                if text and target_lower in text.lower():
                    x = int(data["left"][i] + data["width"][i] / 2)
                    y = int(data["top"][i] + data["height"][i] / 2)
                    return {
                        "x": x,
                        "y": y,
                        "confidence": float(data.get("conf", [0])[i] or 0) / 100.0,
                        "method": "pytesseract",
                        "text": text,
                    }
        except Exception:
            return None
        return None
