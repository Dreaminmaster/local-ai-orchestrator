"""Minimal unified diff applier for single-file patches."""

from __future__ import annotations

import re

HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\s*(.*)$")


def parse_hunks(diff_text: str) -> list[dict]:
    """Parse unified diff hunks from a single diff text."""
    hunks = []
    current = None
    for line in diff_text.splitlines():
        m = HUNK_HEADER.match(line)
        if m:
            if current:
                hunks.append(current)
            current = {
                "old_start": int(m.group(1)),
                "old_count": int(m.group(2) or 1),
                "new_start": int(m.group(3)),
                "new_count": int(m.group(4) or 1),
                "context": m.group(5),
                "operations": [],
            }
        elif current is not None:
            if line.startswith("+"):
                current["operations"].append(("add", line[1:]))
            elif line.startswith("-"):
                current["operations"].append(("remove", line[1:]))
            elif line.startswith(" "):
                current["operations"].append(("keep", line[1:]))
            # skip lines without prefix (e.g. diff metadata, empty lines)
    if current:
        hunks.append(current)
    return hunks


def apply_hunks(
    original_lines: list[str], hunks: list[dict]
) -> tuple[list[str], list[str]]:
    """Apply hunks to original lines. Returns (result_lines, rejections)."""
    result = list(original_lines)
    rejections = []
    # Process hunks from last to first to preserve line numbers
    for hunk in reversed(hunks):
        old_start = hunk["old_start"] - 1
        old_end = old_start + hunk["old_count"]
        ops = hunk["operations"]
        replacement_lines = []
        expected_lines = []  # lines expected at the original location (keep + remove)
        for op, text in ops:
            if op == "keep":
                replacement_lines.append(text + "\n")
                expected_lines.append(text)
            elif op == "remove":
                expected_lines.append(text)
            elif op == "add":
                replacement_lines.append(text + "\n")
        # Verify context: keep + remove lines must match actual slice
        actual_slice = result[old_start:old_end]
        ok = True
        if len(expected_lines) != len(actual_slice):
            ok = False
        else:
            for exp, act in zip(expected_lines, actual_slice):
                if exp.rstrip("\n") != act.rstrip("\n"):
                    ok = False
                    break
        if not ok:
            rejections.append(
                f"hunk @@ -{hunk['old_start']},{hunk['old_count']}"
                f" +{hunk['new_start']},{hunk['new_count']} @@:"
                f" context mismatch"
            )
            continue
        result[old_start:old_end] = replacement_lines
    return result, rejections


def apply_unified_diff(
    original_text: str, diff_text: str
) -> tuple[str, int, list[str]]:
    """Apply a unified diff to original text.
    Returns (patched_text, applied_hunks, rejections).
    """
    hunks = parse_hunks(diff_text)
    if not hunks:
        return original_text, 0, ["no hunks found in diff"]
    orig_lines = original_text.splitlines(keepends=True)
    result_lines, rejections = apply_hunks(orig_lines, hunks)
    applied = len(hunks) - len(rejections)
    return "".join(result_lines), applied, rejections
