from backend.skills.unified_diff_patcher import apply_unified_diff, parse_hunks


def test_single_hunk():
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2_changed\n"
        " line3\n"
    )
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 1
    assert not rejections
    assert result == "line1\nline2_changed\nline3\n"


def test_multi_hunk():
    original = "line1\nline2\nline3\nline4\nline5\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2_changed\n"
        " line3\n"
        "@@ -3,3 +3,3 @@\n"
        " line3\n"
        " line4\n"
        "-line5\n"
        "+line5_changed\n"
    )
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 2
    assert not rejections
    assert result == "line1\nline2_changed\nline3\nline4\nline5_changed\n"


def test_context_mismatch():
    original = "line1\nline2_original\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2_different\n"
        "+line2_changed\n"
        " line3\n"
    )
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 0
    assert len(rejections) == 1
    assert "context mismatch" in rejections[0]


def test_add_only_hunk():
    original = "line1\nline2\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,2 +1,3 @@\n"
        " line1\n"
        "+line_inserted\n"
        " line2\n"
    )
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 1
    assert not rejections
    assert "line_inserted" in result


def test_remove_only_hunk():
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,2 @@\n"
        " line1\n"
        "-line2\n"
        " line3\n"
    )
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 1
    assert not rejections
    assert result == "line1\nline3\n"


def test_no_hunks():
    original = "line1\n"
    diff = "--- a/file.txt\n+++ b/file.txt\n"
    result, applied, rejections = apply_unified_diff(original, diff)
    assert applied == 0
    assert "no hunks" in rejections[0]


def test_parse_hunks_empty():
    hunks = parse_hunks("")
    assert hunks == []
