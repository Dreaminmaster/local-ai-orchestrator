"""Extract actionable patches from external AI / Codex / Claude responses.

Supports:
- ```diff code blocks
- unified diff with file paths
- inline code block with suggested changes
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DIFF_BLOCK = re.compile(r"```(?:diff|patch)\n(.*?)```", re.DOTALL)
CODE_BLOCK = re.compile(r"```(?:python|javascript|js|ts|text)?\n(.*?)```", re.DOTALL)
FILE_PATH = re.compile(
    r"(?:File|file|path)[\s:]+([^\s`\n]+\.(?:py|js|ts|html|css|json|yaml|yml|toml))"
)
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@", re.MULTILINE)


@dataclass
class ExtractedPatch:
    content: str
    format: str  # diff | replace | append | prepend
    file_path: str | None = None
    hunk_count: int = 0
    confidence: float = 0.0
    reject_reason: str | None = None

    def to_file_patch(self) -> str:
        if self.format == "diff":
            return f"unified_diff:{self.content}"
        return self.content

    def to_dict(self) -> dict:
        return {
            "format": self.format,
            "file_path": self.file_path,
            "hunk_count": self.hunk_count,
            "confidence": self.confidence,
            "content_preview": self.content[:500],
            "reject_reason": self.reject_reason,
        }


@dataclass
class PatchExtractionResult:
    patches: list[ExtractedPatch] = field(default_factory=list)
    rejected: list[ExtractedPatch] = field(default_factory=list)
    summary: str = ""
    needs_split: bool = False
    suggested_action: str = ""


class PatchExtractor:
    MAX_CODE_BLOCK_CHARS = 20000

    def extract(self, text: str) -> PatchExtractionResult:
        patches = []
        rejected = []

        # 1. Extract ```diff blocks
        for m in DIFF_BLOCK.finditer(text):
            diff_content = m.group(1).strip()
            if not diff_content:
                continue
            hunk_count = len(HUNK_HEADER.findall(diff_content))
            file_path = self._guess_file_path(text, m.start())
            patch = ExtractedPatch(
                content=diff_content,
                format="diff",
                file_path=file_path,
                hunk_count=hunk_count,
                confidence=min(hunk_count / 3.0, 1.0) if hunk_count > 0 else 0.3,
            )
            if hunk_count > 0:
                patches.append(patch)
            else:
                patch.reject_reason = "No @@ hunk headers found in diff block"
                rejected.append(patch)

        # 2. If no diff blocks, extract code blocks as possible replacements
        if not patches:
            for m in CODE_BLOCK.finditer(text):
                code = m.group(1).strip()
                if not code or len(code) > self.MAX_CODE_BLOCK_CHARS:
                    continue
                file_path = self._guess_file_path(text, m.start())
                patch = ExtractedPatch(
                    content=code,
                    format="replace",
                    file_path=file_path,
                    hunk_count=0,
                    confidence=0.4,
                )
                patches.append(patch)
                break

        # 3. If still nothing, look for simple prepend/append patterns
        if not patches:
            prepend = re.search(
                r"(?:add|prepend|insert)\s*(?:at top|before all)[\s:]*(.+)",
                text,
                re.IGNORECASE,
            )
            if prepend:
                patches.append(
                    ExtractedPatch(
                        content=f"prepend:{prepend.group(1).strip()}",
                        format="prepend",
                        confidence=0.5,
                    )
                )

        summary = (
            f"Extracted {len(patches)} patches ({len(rejected)} rejected)"
            if patches
            else "No patches extracted from response"
        )
        needs_split = len([p for p in patches if p.format == "diff"]) > 1
        suggested_action = "split_into_single_file_patches" if needs_split else ""
        return PatchExtractionResult(
            patches=patches,
            rejected=rejected,
            summary=summary,
            needs_split=needs_split,
            suggested_action=suggested_action,
        )

    def _guess_file_path(self, text: str, near_pos: int) -> str | None:
        """Guess file path from nearby context."""
        window = text[max(0, near_pos - 200) : near_pos + 200]
        m = FILE_PATH.search(window)
        if m:
            return m.group(1)
        # Also check the full text for a single file path
        all_files = FILE_PATH.findall(text[:2000])
        if len(all_files) == 1:
            return all_files[0]
        return None
