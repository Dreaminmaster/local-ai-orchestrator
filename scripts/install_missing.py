#!/usr/bin/env python3
"""Install missing project dependencies. Never installs system tools.

Only handles:
- venv
- pip requirements (fastapi, uvicorn, httpx, etc.)
- Playwright Chromium (to .playwright-browsers/)
- .env (from .env.example)
- runtime/ directories
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IS_WIN = sys.platform == "win32"
VENV_PY = ROOT / ("venv/Scripts/python.exe" if IS_WIN else "venv/bin/python")
VENV_PIP = ROOT / ("venv/Scripts/pip" if IS_WIN else "venv/bin/pip")


def confirm(prompt: str) -> bool:
    ans = input(f"{prompt} [y/N] ").strip().lower()
    return ans in ("y", "yes")


def run(cmd, desc="", check=True):
    print(f"  ⚡ {desc or cmd}")
    try:
        subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=not isinstance(cmd, list),
            cwd=str(ROOT),
            check=check,
            env={
                **os.environ,
                "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".playwright-browsers"),
            },
        )
        return True
    except subprocess.CalledProcessError:
        print(f"  ❌ 失败: {desc}")
        return False


def main():
    print("🧠 Local AI Orchestrator — 安装缺失项目依赖")
    print(f"   项目目录: {ROOT}")
    print()

    tasks = []

    # venv
    if not VENV_PY.exists():
        tasks.append(("venv", "python -m venv venv"))
    else:
        print("  ✅ venv 已存在")

    # pip
    if VENV_PY.exists():
        try:
            subprocess.run(
                [str(VENV_PY), "-c", "import fastapi, uvicorn, httpx"],
                capture_output=True,
                timeout=10,
            )
            print("  ✅ Python 依赖已安装")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            tasks.append(
                ("pip 依赖", [str(VENV_PIP), "install", "-r", "requirements.txt"])
            )
    else:
        tasks.append(
            ("pip 依赖 (需 venv)", [str(VENV_PIP), "install", "-r", "requirements.txt"])
        )

    # Playwright Chromium
    pw_dir = ROOT / ".playwright-browsers"
    pw_installed = pw_dir.exists() and any(pw_dir.glob("chromium-*"))
    if pw_installed:
        print(f"  ✅ Playwright Chromium: {pw_dir}")
    else:
        try:
            import playwright  # noqa: F401

            has_lib = True
        except ImportError:
            has_lib = False
        if has_lib:
            tasks.append(
                (
                    "Playwright Chromium",
                    [str(VENV_PY), "-m", "playwright", "install", "chromium"],
                )
            )
        else:
            print("  ⚠️  Playwright 库未安装，跳过 Chromium。安装 pip 依赖后再试。")

    # .env
    if not (ROOT / ".env").exists():
        tasks.append((".env 文件", "cp .env.example .env"))
    else:
        print("  ✅ .env 已存在")

    # runtime
    if not (ROOT / "runtime").exists():
        tasks.append(
            (
                "runtime 目录",
                "mkdir -p runtime/evidence runtime/tasks runtime/test_reports",
            )
        )
    else:
        print("  ✅ runtime 目录已存在")

    if not tasks:
        print("\n✅ 所有项目依赖已就绪！")
        return

    print(f"\n📋 将安装以下 {len(tasks)} 项：")
    for name, _ in tasks:
        print(f"  - {name}")
    print()

    if not confirm("是否继续安装？"):
        print("取消。")
        return

    for name, cmd in tasks:
        print(f"\n📦 {name} ...")
        if not run(cmd, name):
            print(f"  ❌ {name} 安装失败，跳过。")

    print("\n── Doctor 检查 ──")
    subprocess.run([sys.executable, str(ROOT / "scripts/doctor.py")])


if __name__ == "__main__":
    main()
