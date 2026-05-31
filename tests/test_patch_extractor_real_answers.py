"""Test PatchExtractor against realistic external AI answers."""

from pathlib import Path

from backend.core.patch_extractor import PatchExtractor

FIXTURES = Path(__file__).resolve().parent / "fixtures/external_ai_answers"


def test_chatgpt_diff():
    text = (FIXTURES / "chatgpt_diff.md").read_text(encoding="utf-8")
    result = PatchExtractor().extract(text)
    assert result.patches
    assert result.patches[0].format == "diff"
    assert result.patches[0].hunk_count == 1


def test_claude_explanation_plus_diff():
    text = (FIXTURES / "claude_explanation_plus_diff.md").read_text(encoding="utf-8")
    result = PatchExtractor().extract(text)
    assert result.patches
    assert result.patches[0].format == "diff"
    assert result.patches[0].hunk_count == 1


def test_codex_patch():
    text = (FIXTURES / "codex_patch.md").read_text(encoding="utf-8")
    result = PatchExtractor().extract(text)
    assert result.patches
    assert result.patches[0].format == "diff"
    assert result.patches[0].hunk_count == 1


def test_plain_text_steps():
    text = (FIXTURES / "plain_text_steps.md").read_text(encoding="utf-8")
    result = PatchExtractor().extract(text)
    # No diff blocks, should extract replace from the longer text
    extract = result.patches[0] if result.patches else None
    if extract:
        assert extract.format != "diff"  # plain text can't produce diff
    # At minimum the result summary should be produced
    assert result.summary


def test_multi_file_diff():
    text = (FIXTURES / "multi_file_diff.md").read_text(encoding="utf-8")
    result = PatchExtractor().extract(text)
    # Multiple diff blocks → multiple patches
    assert len(result.patches) >= 2
    for p in result.patches:
        assert p.format == "diff"
    # Each diff should have exactly one hunk
    assert all(p.hunk_count == 1 for p in result.patches)
    # Needs_split flag for multi-file
    assert len(result.patches) > 1
