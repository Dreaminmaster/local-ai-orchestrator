import shutil

import pytest

from backend.skills.desktop_visual.backends.ocr_backend import OCRBackend


def test_ocr_backend_locates_submit(tmp_path):
    if not shutil.which("tesseract"):
        pytest.skip("tesseract binary is not installed")
    try:
        from PIL import Image, ImageDraw
        import pytesseract  # noqa: F401
    except Exception as exc:
        pytest.skip(f"OCR dependencies unavailable: {exc}")

    img = Image.new("RGB", (320, 120), "white")
    draw = ImageDraw.Draw(img)
    draw.text((80, 45), "Submit", fill="black")
    path = tmp_path / "submit.png"
    img.save(path)

    result = OCRBackend().locate(str(path), "Submit")
    assert result is not None
    assert 0 <= result["x"] <= 320
    assert 0 <= result["y"] <= 120
