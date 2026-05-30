class OCRLocator:
    """OCR-based locator placeholder.

    If pytesseract/easyocr/apple-vision is available in a deployment, plug it here.
    Returns None when OCR backend is not configured.
    """

    def locate_text(self, screenshot_path: str, text: str) -> dict | None:
        return None
