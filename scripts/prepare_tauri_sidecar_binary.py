#!/usr/bin/env python3
"""Prepare a target-triple named Tauri sidecar binary.

This script copies the local PyInstaller prototype binary into the filename
shape Tauri expects for formal sidecar lookup. It does not build or package
the app, and the generated binary remains ignored.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "apps/desktop/src-tauri/bin"
BASE_NAME = "local-ai-orchestrator-backend"
SOURCE = BIN_DIR / BASE_NAME
ONEDIR_SOURCE = BIN_DIR / f"{BASE_NAME}-dir" / BASE_NAME
MACOS_TARGETS = ("aarch64-apple-darwin", "x86_64-apple-darwin")


def _host_target() -> str:
    rustc = os.environ.get("RUSTC", "rustc")
    try:
        proc = subprocess.run(
            [rustc, "-vV"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"{rustc} not found") from exc
    if proc.returncode != 0:
        raise RuntimeError(
            "rustc -vV failed; put Rust/Cargo on PATH before preparing the sidecar name. "
            f"stderr={proc.stderr.strip()}"
        )
    for line in proc.stdout.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("Could not find host target in rustc -vV output")


def _command_output(command: list[str]) -> str:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _auto_targets() -> list[str]:
    candidates: list[str] = []

    env_target = os.environ.get("TAURI_BUILD_TARGET") or os.environ.get("CARGO_BUILD_TARGET")
    if env_target:
        candidates.append(env_target)

    rust_host = ""
    try:
        rust_host = _host_target()
        candidates.append(rust_host)
    except RuntimeError:
        pass

    machine = _command_output(["uname", "-m"]) or _command_output(["arch"])
    node_arch = _command_output(["node", "-p", "process.arch"])
    if machine == "arm64" or node_arch == "arm64":
        candidates.insert(0, "aarch64-apple-darwin")
    elif machine == "x86_64" or node_arch == "x64":
        candidates.insert(0, "x86_64-apple-darwin")

    seen = set()
    unique = []
    for target in candidates:
        if target and target not in seen:
            seen.add(target)
            unique.append(target)
    return unique


def _copy_for_target(target: str) -> Path:
    suffix = ".exe" if target.endswith("windows-msvc") else ""
    destination = BIN_DIR / f"{BASE_NAME}-{target}{suffix}"
    shutil.copy2(SOURCE, destination)
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return destination


def main() -> int:
    parser = ArgumentParser(description="Prepare target-triple Tauri sidecar binaries")
    parser.add_argument(
        "--target",
        action="append",
        choices=[*MACOS_TARGETS, "x86_64-pc-windows-msvc"],
        help="target triple to generate; can be provided more than once",
    )
    parser.add_argument(
        "--mode",
        choices=("onefile", "onedir"),
        default="onefile",
        help="source layout; onedir is reported for packaged smoke and is not copied as externalBin",
    )
    parser.add_argument("--auto", action="store_true", help="detect likely Tauri build target")
    parser.add_argument(
        "--all-macos",
        action="store_true",
        help="generate both macOS sidecar target names",
    )
    args = parser.parse_args()

    source = SOURCE if args.mode == "onefile" else ONEDIR_SOURCE
    if not source.exists():
        print(f"Backend binary missing: {source}")
        print(
            f"Run scripts/build_backend_binary.py --mode {args.mode} first, "
            "then rerun this script."
        )
        return 2

    if args.mode == "onedir":
        print(f"mode=onedir")
        print(f"onedir_executable={source}")
        print(
            "strategy=dev-known-path; onedir dependencies must remain beside the executable, "
            "so no target-triple externalBin copy is generated"
        )
        return 0

    targets = args.target or []
    if args.all_macos:
        targets.extend(MACOS_TARGETS)
    if args.auto:
        targets.extend(_auto_targets())

    if not targets:
        print("No target selected.")
        print("Use one of:")
        for target in (*MACOS_TARGETS, "x86_64-pc-windows-msvc"):
            print(f"  --target {target}")
        print("Or use --auto after confirming the active Tauri build target.")
        return 2

    unique_targets = []
    seen = set()
    for target in targets:
        if target not in seen:
            seen.add(target)
            unique_targets.append(target)

    try:
        host_target = _host_target()
    except RuntimeError as exc:
        host_target = f"unknown ({exc})"
    print(f"rust_host_target={host_target}")
    print(f"auto_candidates={_auto_targets()}")
    print(f"source={source}")
    for target in unique_targets:
        destination = _copy_for_target(target)
        print(f"sidecar_binary={destination}")
        print(f"target={target}")
        print(f"size={destination.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
