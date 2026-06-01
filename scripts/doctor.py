#!/usr/bin/env python3
"""Deployment doctor — checks what's installed, what's missing.

System tools (only detected, never auto-installed):
  Python, Git, LM Studio, Ollama, Node.js

Project dependencies (can be installed by install_missing.py):
  venv, pip packages, Playwright Chromium, .env, runtime dirs
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IS_WIN = sys.platform == "win32"

results = []


def add(label, ok, category, fix=""):
    results.append({"label": label, "ok": ok, "category": category, "fix": fix})
    icon = "✅" if ok else "❌"
    suffix = f" → {fix}" if fix else ""
    print(f"  {icon} [{category}] {label}{suffix}")


print("🧠 Local AI Orchestrator — Doctor")
print(f"   项目目录: {ROOT}")
print()

# ── SYSTEM TOOLS ──
print("── 系统工具 ──")
py_ok = sys.version_info >= (3, 10)
add(
    f"Python >= 3.10 ({sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})",
    py_ok,
    "system",
    "Install from python.org" if not py_ok else "",
)

git_ok = shutil.which("git") is not None
add("Git", git_ok, "system", "Install from git-scm.com" if not git_ok else "")

# LM Studio
lm_ok = False
try:
    import urllib.request

    urllib.request.urlopen("http://localhost:1234/v1/models", timeout=3)
    lm_ok = True
except Exception:
    pass
add(
    "LM Studio (port 1234)",
    lm_ok,
    "system",
    "Open LM Studio → Developer → Start Server" if not lm_ok else "",
)

# Ollama
ol_ok = False
try:
    import urllib.request

    urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    ol_ok = True
except Exception:
    pass
add(
    "Ollama (port 11434)",
    ol_ok,
    "system",
    "Run: ollama serve && ollama pull llama3" if not ol_ok else "",
)

# ── PROJECT DEPENDENCIES ──
print("\n── 项目依赖 ──")
venv_python = ROOT / ("venv/Scripts/python.exe" if IS_WIN else "venv/bin/python")
venv_ok = venv_python.exists()
add(
    "venv (虚拟环境)",
    venv_ok,
    "project",
    "Run: python -m venv venv" if not venv_ok else "",
)

# pip requirements
req_ok = False
if venv_ok:
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import fastapi, uvicorn, httpx"],
            capture_output=True,
            timeout=10,
            cwd=str(ROOT),
        )
        req_ok = result.returncode == 0
    except Exception:
        req_ok = False
add(
    "Python 项目依赖 (requirements.txt)",
    req_ok,
    "project",
    "Run: pip install -r requirements.txt" if not req_ok else "",
)

# Playwright
pw_browsers_path = os.environ.get(
    "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers")
)
pw_dir = Path(pw_browsers_path)
pw_ok = False
if pw_dir.exists() and any(pw_dir.glob("chromium-*")):
    pw_ok = True
else:
    try:
        import playwright  # noqa: F401

        pw_ok = True  # library installed, browser check later
    except ImportError:
        pw_ok = False
add(
    f"Playwright Chromium ({pw_dir})",
    pw_ok,
    "project",
    (
        "Run: PLAYWRIGHT_BROWSERS_PATH=.playwright-browsers playwright install chromium"
        if not pw_ok
        else ""
    ),
)

# .env
env_ok = (ROOT / ".env").exists()
add(
    ".env 配置文件",
    env_ok,
    "project",
    "Run: cp .env.example .env" if not env_ok else "已存在",
)

# runtime dirs
runtime_ok = all((ROOT / d).exists() for d in ["runtime"])
add(
    "runtime 运行目录",
    runtime_ok,
    "project",
    (
        "Run: mkdir -p runtime/evidence runtime/tasks runtime/test_reports"
        if not runtime_ok
        else ""
    ),
)

# Port
port_free = True
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect(("127.0.0.1", 8422))
    s.close()
    port_free = False
except Exception:
    pass
add(
    "端口 8422 可用",
    port_free,
    "system",
    "端口被占用。关闭占用进程或改 .env 中的 PORT" if not port_free else "",
)

# ── OPTIONAL ──
print("\n── 可选项 ──")
profile_path = ROOT / "runtime/test_reports/web_ai/profile_status.json"
web_ok = False
if profile_path.exists():
    import json

    profiles = json.loads(profile_path.read_text(encoding="utf-8"))
    logged = [p for p, s in profiles.items() if s.get("logged_in")]
    web_ok = bool(logged)
    add(
        f"Web AI 登录态 ({', '.join(logged) if logged else '无'})",
        web_ok,
        "optional",
        (
            "Run: python scripts/init_web_ai_profile.py --provider chatgpt"
            if not web_ok
            else ""
        ),
    )
else:
    add(
        "Web AI 登录态",
        False,
        "optional",
        "Run: python scripts/init_web_ai_profile.py --provider chatgpt",
    )

# ── SUMMARY ──
print("\n" + "=" * 48)
by_cat = {}
for r in results:
    by_cat.setdefault(r["category"], []).append(r)
for cat in ["system", "project", "optional"]:
    items = by_cat.get(cat, [])
    ok = sum(1 for x in items if x["ok"])
    total = len(items)
    print(f"  [{cat}] {ok}/{total}")

sys_ok = all(r["ok"] for r in results if r["category"] == "system")
proj_ok = all(r["ok"] for r in results if r["category"] == "project")
total_ok = sum(1 for r in results if r["ok"])

if not sys_ok:
    missing_sys = [
        r["label"] for r in results if r["category"] == "system" and not r["ok"]
    ]
    print(f"\n⚠️  系统工具缺失: {', '.join(missing_sys)}")
    print("   请手动安装这些系统工具后重新运行 doctor。")
if not proj_ok:
    missing_proj = [
        r["label"] for r in results if r["category"] == "project" and not r["ok"]
    ]
    print(f"\n⚠️  项目依赖缺失: {', '.join(missing_proj)}")
    print("   运行: python scripts/install_missing.py")
if sys_ok and proj_ok:
    print("\n✅ 环境就绪！运行: ./scripts/start_local.sh")
else:
    print(f"\n{total_ok}/{len(results)} 项通过")
