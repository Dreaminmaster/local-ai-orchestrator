"""Secret scanner and redactor used before sending content to external AI.

This is a non-blocking safety layer:
scan -> redact -> send redacted content -> save sanitized evidence -> continue.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SecretScanResult:
    has_secrets: bool
    findings: list[str]
    counts: dict[str, int] = field(default_factory=dict)


@dataclass
class RedactionResult:
    original_had_secrets: bool
    redacted_text: str
    findings: list[str]
    counts: dict[str, int]
    redacted: bool


class SecretScanner:
    PATTERNS = {
        "openai_api_key_env": r"(?i)OPENAI_API_KEY\s*=\s*['\"]?[^\s'\"]+",
        "anthropic_api_key_env": r"(?i)ANTHROPIC_API_KEY\s*=\s*['\"]?[^\s'\"]+",
        "generic_api_key_env": r"(?i)(API_KEY|[A-Z0-9_]*_API_KEY)\s*=\s*['\"]?[^\s'\"]+",
        "sk_key": r"sk-[A-Za-z0-9_-]{16,}",
        "token_env": r"(?i)(token|access_token|refresh_token)\s*=\s*['\"]?[^\s'\"]+",
        "secret_env": r"(?i)(secret|client_secret)\s*=\s*['\"]?[^\s'\"]+",
        "password_env": r"(?i)(password|passwd|pwd)\s*=\s*['\"]?[^\s'\"]+",
        "database_url": r"(?i)DATABASE_URL\s*=\s*['\"]?[^\s'\"]+|[a-z]+://[^\s:@]+:[^\s:@]+@[^\s]+",
        "private_key_block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
        "ssh_private_key": r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----",
        "env_file_content": r"(?m)^(?:[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|DATABASE_URL)[A-Z0-9_]*)\s*=.+$",
        "mnemonic_or_seed_phrase": r"(?i)(mnemonic|seed phrase|助记词|private key).{0,80}",
        "github_token": r"gh[pousr]_[A-Za-z0-9_]{20,}",
        "jwt": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    }

    def scan(self, text: str) -> SecretScanResult:
        findings: list[str] = []
        counts: dict[str, int] = {}
        for name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text or "")
            if matches:
                findings.append(name)
                counts[name] = len(matches)
        return SecretScanResult(bool(findings), findings, counts)

    def redact(self, text: str) -> RedactionResult:
        redacted_text = text or ""
        findings: list[str] = []
        counts: dict[str, int] = {}
        for name, pattern in self.PATTERNS.items():
            redacted_text, count = re.subn(pattern, f"[REDACTED:{name}]", redacted_text)
            if count:
                findings.append(name)
                counts[name] = count
        return RedactionResult(
            original_had_secrets=bool(findings),
            redacted_text=redacted_text,
            findings=findings,
            counts=counts,
            redacted=bool(findings),
        )

    def redact_file_text(self, path: str, max_chars: int = 20000) -> RedactionResult:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return self.redact("")
        return self.redact(p.read_text(encoding="utf-8", errors="replace")[:max_chars])

    def evidence_summary(self, result: RedactionResult) -> dict:
        """Safe summary for Evidence Board. Never includes raw secret values."""
        return {
            "secret_categories_found": result.findings,
            "counts": result.counts,
            "redacted": result.redacted,
            "sent_to_external_ai": (
                "redacted_version"
                if result.redacted
                else "original_no_secrets_detected"
            ),
        }
