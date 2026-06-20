#!/usr/bin/env python3
"""Audit a macOS .app bundle for Apple Silicon compatibility."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout.strip()


def _classify_arch(file_output: str, lipo_output: str) -> dict:
    text = f"{file_output}\n{lipo_output}".lower()
    arm64 = "arm64" in text or "arm64e" in text
    x86_64 = "x86_64" in text
    universal = "universal binary" in text or "are:" in text
    universal2 = universal and arm64 and x86_64
    if universal2:
        architecture = "universal2"
    elif arm64 and not x86_64:
        architecture = "arm64"
    elif x86_64 and not arm64:
        architecture = "x86_64"
    elif "mach-o" in text:
        architecture = "unknown_macho"
    else:
        architecture = "not_macho"
    allowed = architecture in {"arm64", "universal2"}
    required_action = "" if allowed else "replace_with_arm64_or_universal2"
    return {
        "architecture": architecture,
        "arm64": arm64,
        "x86_64": x86_64,
        "universal2": universal2,
        "allowed": allowed,
        "required_action": required_action,
    }


def _origin(path: Path) -> str:
    parts = path.parts
    joined = "/".join(parts)
    if "/Contents/MacOS/" in joined:
        return "tauri_macos_executable"
    if "/Contents/Resources/bin/local-ai-orchestrator-backend-dir/" in joined:
        return "pyinstaller_onedir_sidecar"
    if "/Contents/Resources/bin/" in joined:
        return "tauri_sidecar_resource"
    if "/Contents/Frameworks/" in joined:
        return "tauri_framework"
    if "/Contents/Resources/" in joined:
        return "app_resource"
    return "app_bundle"


def audit(app: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(p for p in app.rglob("*") if p.is_file()):
        rc, file_output = _run(["file", str(path)])
        if rc != 0:
            continue
        if "Mach-O" not in file_output and "universal binary" not in file_output:
            continue
        _, lipo_output = _run(["lipo", "-info", str(path)])
        arch = _classify_arch(file_output, lipo_output)
        rows.append(
            {
                "path": str(path),
                "relative_path": str(path.relative_to(app)),
                "file_type": file_output.split(":", 1)[1].strip() if ":" in file_output else file_output,
                "lipo_info": lipo_output,
                "build_origin": _origin(path),
                **arch,
            }
        )
    return rows


def write_markdown(path: Path, app: Path, rows: list[dict]) -> None:
    failures = [row for row in rows if not row["allowed"]]
    lines = [
        "# Apple Silicon Bundle Architecture Audit",
        "",
        f"App: `{app}`",
        f"Mach-O files scanned: `{len(rows)}`",
        f"x86_64-only / disallowed files: `{len(failures)}`",
        f"Result: `{'PASS' if not failures else 'FAIL'}`",
        "",
        "## Disallowed Files",
        "",
    ]
    if failures:
        lines.append("| Path | Architecture | Origin | Required action |")
        lines.append("| --- | --- | --- | --- |")
        for row in failures:
            lines.append(
                f"| `{row['relative_path']}` | `{row['architecture']}` | "
                f"`{row['build_origin']}` | `{row['required_action']}` |"
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Full Mach-O Manifest", ""])
    lines.append("| Path | Architecture | Origin |")
    lines.append("| --- | --- | --- |")
    for row in rows:
        lines.append(
            f"| `{row['relative_path']}` | `{row['architecture']}` | `{row['build_origin']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit .app Mach-O architectures")
    parser.add_argument("app", type=Path, help="Path to .app bundle")
    parser.add_argument("--json-out", type=Path, default=Path("macos_bundle_architecture_audit.json"))
    parser.add_argument("--md-out", type=Path, default=Path("APPLE_SILICON_ARCHITECTURE_AUDIT_REPORT.md"))
    args = parser.parse_args()

    app = args.app.resolve()
    if not app.exists() or app.suffix != ".app":
        print(f"App bundle not found: {app}", file=sys.stderr)
        return 2
    rows = audit(app)
    failures = [row for row in rows if not row["allowed"]]
    payload = {
        "app": str(app),
        "macho_count": len(rows),
        "failure_count": len(failures),
        "result": "PASS" if not failures else "FAIL",
        "failures": failures,
        "files": rows,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.md_out, app, rows)
    print(json.dumps({k: payload[k] for k in ("result", "macho_count", "failure_count")}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
