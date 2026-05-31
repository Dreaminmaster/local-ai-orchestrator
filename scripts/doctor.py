#!/usr/bin/env python3
"""Deployment health check — tells you what's working and what needs fixing."""

from __future__ import annotations

import importlib
import os
import shutil
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = []


def check(name: str, ok: bool, fix: str = ""):
    CHECKS.append((name, ok, fix))
    icon = "✅" if ok else "❌"
    msg = f"  {icon} {name}"
    if fix:
        msg += f"  → {fix}"
    print(msg)


print("🧠 Local AI Orchestrator — Doctor Check")
print("========================================\n")

# Python
py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
py_ok = sys.version_info >= (3, 10)
check(
    "Python >= 3.10",
    py_ok,
    f"Current: {py_ver}. Install from python.org" if not py_ok else f"Python {py_ver}",
)

# Virtual env
venv_ok = (ROOT / "venv/bin/python").exists() or (
    ROOT / "venv/Scripts/python.exe"
).exists()
check("Virtual environment (venv)", venv_ok, "Run: python3 -m venv venv")

# Requirements
try:
    import fastapi  # noqa: F401
    import uvicorn  # noqa: F401

    req_ok = True
except ImportError:
    req_ok = False
check("Python dependencies", req_ok, "Run: pip install -r requirements.txt")

# Playwright
pw_ok = shutil.which("chromium") is not None or (
    Path.home() / ".cache/ms-playwright" / "chromium-*"
    if os.name != "nt"
    else Path(os.environ.get("USERPROFILE", "~")) / "AppData/Local/ms-playwright"
)  # approximate; actual check:
try:
    import playwright  # noqa: F401

    pw_ok = True
except ImportError:
    pw_ok = False
check("Playwright", pw_ok, "Run: playwright install chromium")

# .env
env_path = ROOT / ".env"
env_ok = env_path.exists()
check(
    ".env file",
    env_ok,
    "Run: cp .env.example .env" + (" (then edit LLM config)" if not env_ok else ""),
)

# Runtime directories
runtime_ok = all((ROOT / d).exists() for d in ["runtime/evidence", "runtime/tasks"])
check("Runtime directories", runtime_ok, "Run: mkdir -p runtime/evidence runtime/tasks")

# Port 8422
port_free = True
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect(("127.0.0.1", 8422))
    sock.close()
    port_free = False
except Exception:
    pass
check(
    "Port 8422 available",
    port_free,
    "Port 8422 is in use. Kill the process or change PORT in .env",
)

# LM Studio connectivity
lm_ok = False
try:
    import httpx

    async def _check_lm():
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get("http://localhost:1234/v1/models")
            return r.status_code == 200

    # Use sync version since we can't run async easily here
    import urllib.request

    req = urllib.request.Request("http://localhost:1234/v1/models")
    urllib.request.urlopen(req, timeout=3)
    lm_ok = True
except Exception:
    pass
check("LM Studio (http://localhost:1234)", lm_ok, "Start LM Studio and load a model")

# Ollama
ol_ok = False
try:
    import urllib.request

    urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    ol_ok = True
except Exception:
    pass
check(
    "Ollama (http://localhost:11434)",
    ol_ok,
    "Start Ollama and pull a model: ollama pull llama3",
)

# Web AI profiles
profile_status_path = ROOT / "runtime/test_reports/web_ai/profile_status.json"
if profile_status_path.exists():
    import json

    profiles = json.loads(profile_status_path.read_text(encoding="utf-8"))
    logged_in = [p for p, s in profiles.items() if s.get("logged_in")]
    check(
        "Web AI profiles",
        bool(logged_in),
        (
            f"Logged in: {', '.join(logged_in)}"
            if logged_in
            else "No logged-in profiles. Run: python scripts/init_web_ai_profile.py --provider chatgpt"
        ),
    )
else:
    check(
        "Web AI profiles",
        False,
        "Run: python scripts/init_web_ai_profile.py --provider chatgpt",
    )

# Backend import
try:
    importlib.import_module("backend.main")
    backend_ok = True
except Exception as e:
    backend_ok = False
    check("Backend import", False, f"Backend code has errors: {e}")

print("\n========================================")
ok_count = sum(1 for _, ok, _ in CHECKS if ok)
total = len(CHECKS)
print(f"Summary: {ok_count}/{total} checks passed\n")

if ok_count == total:
    print("✅ All checks passed! Run: python -m backend.main")
elif ok_count >= total - 2:
    print("⚠️  Most checks passed. Fix the ❌ items above and try again.")
else:
    print("❌ Several checks failed. Follow the fix suggestions above.")
