#!/usr/bin/env python3
"""Build the backend sidecar prototype with PyInstaller.

This script intentionally does not install PyInstaller. It only uses the
current Python environment if PyInstaller is already available.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "apps/desktop/src-tauri/bin"
BUILD_DIR = ROOT / "build/backend_binary"
ENTRY = ROOT / "backend/sidecar_entry.py"
BINARY_NAME = "local-ai-orchestrator-backend"
ONEDIR_NAME = f"{BINARY_NAME}-dir"


def _pyinstaller_available() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = (proc.stdout or proc.stderr).strip()
    return proc.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build backend sidecar prototype")
    parser.add_argument("--clean", action="store_true", help="remove prior build cache first")
    parser.add_argument(
        "--mode",
        choices=("onefile", "onedir"),
        default="onefile",
        help="PyInstaller output mode; onedir is preferred for packaged startup diagnostics",
    )
    args = parser.parse_args()

    available, version = _pyinstaller_available()
    if not available:
        print("PyInstaller missing")
        print(f"Python: {sys.executable}")
        print("Install PyInstaller into the project venv or approved build venv first.")
        print("Suggested after confirmation: venv/bin/pip install pyinstaller")
        print("No install was attempted.")
        return 2

    print(f"PyInstaller: {version}")
    print(f"Python: {sys.executable}")

    if args.clean and BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    mode_flag = "--onefile" if args.mode == "onefile" else "--onedir"
    dist_path = BIN_DIR if args.mode == "onefile" else BUILD_DIR / "dist_onedir"
    onedir_output = BIN_DIR / ONEDIR_NAME
    if args.mode == "onedir":
        shutil.rmtree(dist_path, ignore_errors=True)
        shutil.rmtree(onedir_output, ignore_errors=True)
        dist_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        mode_flag,
        "--name",
        BINARY_NAME,
        "--distpath",
        str(dist_path),
        "--workpath",
        str(BUILD_DIR / "work"),
        "--specpath",
        str(BUILD_DIR),
        "--paths",
        str(ROOT),
        str(ENTRY),
    ]
    print("Running:")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        return proc.returncode

    if args.mode == "onedir":
        generated_dir = dist_path / BINARY_NAME
        if not generated_dir.exists():
            print(f"Expected onedir output missing: {generated_dir}")
            return 3
        shutil.move(str(generated_dir), str(onedir_output))
        binary = onedir_output / BINARY_NAME
        print(f"Onedir: {onedir_output}")
    else:
        binary = BIN_DIR / BINARY_NAME

    print(f"Mode: {args.mode}")
    print(f"Binary: {binary}")
    if binary.exists():
        print(f"Size: {binary.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
