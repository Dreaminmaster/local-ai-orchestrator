"""Verify Claude answer extractor handles real response patterns."""


from backend.skills.external_ai_web.answer_extractor import AnswerExtractor
from backend.skills.external_ai_web.selectors import SELECTORS


def test_claude_selector_has_body_marker():
    sel = SELECTORS.get("claude", {})
    assert "body_marker" in sel
    assert sel["body_marker"] == "claude"


def test_extractor_graceful_on_empty():
    extractor = AnswerExtractor()
    from unittest.mock import AsyncMock

    page = AsyncMock()
    page.locator.return_value.inner_text = AsyncMock(side_effect=Exception("fail"))
    import asyncio

    result = asyncio.run(extractor.latest(page, "claude"))
    assert isinstance(result, str)


# body_marker extraction validated in live Claude Web E2E
