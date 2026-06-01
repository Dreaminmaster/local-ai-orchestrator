"""Verify Claude answer extractor handles real response patterns."""


from backend.skills.external_ai_web.answer_extractor import AnswerExtractor
from backend.skills.external_ai_web.selectors import SELECTORS


def test_claude_selector_has_body_marker():
    sel = SELECTORS.get("claude", {})
    assert "body_marker" in sel
    assert sel["body_marker"] == "claude"


def test_body_marker_extracts_tail():
    extractor = AnswerExtractor()
    full_body = "Header\n\nUser: hello\n\nAssistant: Hello from claude\n\nText"
    from unittest.mock import AsyncMock

    page = AsyncMock()
    page.locator.return_value.count = AsyncMock(return_value=0)
    page.locator.return_value.inner_text = AsyncMock(return_value=full_body)
    import asyncio

    result = asyncio.run(extractor.latest(page, "claude"))
    assert "claude" in result.lower()


def test_extractor_graceful_on_empty():
    extractor = AnswerExtractor()
    from unittest.mock import AsyncMock

    page = AsyncMock()
    page.locator.return_value.inner_text = AsyncMock(side_effect=Exception("fail"))
    import asyncio

    result = asyncio.run(extractor.latest(page, "claude"))
    assert isinstance(result, str)
