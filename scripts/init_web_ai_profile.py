#!/usr/bin/env python3
"""Initialize a persistent Web AI browser profile.

Usage:
    PYTHONPATH=. python scripts/init_web_ai_profile.py --provider chatgpt
    PYTHONPATH=. python scripts/init_web_ai_profile.py --provider claude

This opens the provider webpage using Playwright persistent context.
Log in manually, then press Enter to detect login state and save status.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "runtime/test_reports/web_ai/profile_status.json"
PROFILE_DIR = ROOT / "runtime/browser_profiles"

URLS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/new",
    "doubao": "https://www.doubao.com/chat/",
    "gemini": "https://gemini.google.com/app",
    "kimi": "https://www.kimi.com/",
}

LOGIN_GATES = {
    "chatgpt": "textarea, [contenteditable='true']",
    "claude": "div[contenteditable='true'], textarea",
    "doubao": "textarea, [contenteditable='true']",
    "gemini": "rich-textarea div[contenteditable='true'], textarea",
    "kimi": "textarea, [contenteditable='true']",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize a Web AI persistent profile"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["chatgpt", "claude", "doubao", "gemini", "kimi"],
        help="Which provider to initialize",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    provider = args.provider
    url = URLS[provider]
    profile_dir = PROFILE_DIR / provider
    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🌐 Opening {provider} ({url})")
    print(f"   Profile directory: {profile_dir}")
    print("   A browser window will open. Please log in manually.")
    print("   After you have finished logging in, come back to this terminal.\n")

    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 1000},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        input("\n🔑 Log in, then press Enter to continue...\n")

        # Detect login state
        selector = LOGIN_GATES[provider]
        try:
            input_box = page.locator(selector).last
            has_input = await input_box.count() > 0
        except Exception:
            has_input = False

        url_lower = page.url.lower()
        is_login_page = any(
            w in url_lower for w in ["login", "signin", "auth", "register"]
        )
        page_text = ""
        try:
            page_text = (await page.locator("body").inner_text(timeout=5000)).lower()[
                :2000
            ]
        except Exception:
            pass
        captcha_or_gate = any(
            w in page_text for w in ["login", "sign in", "登录", "注册", "captcha"]
        )
        logged_in = has_input and not is_login_page and not captcha_or_gate

        status = {
            "provider": provider,
            "profile_dir": str(profile_dir),
            "logged_in": logged_in,
            "url": page.url,
            "has_input_box": has_input,
            "is_login_page": is_login_page,
            "initialized_at": datetime.now().isoformat(),
        }

        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if STATUS_PATH.exists():
            existing = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        existing[provider] = status
        STATUS_PATH.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        await context.close()

        state_label = "✅ LOGGED IN" if logged_in else "⚠️  LOGIN NOT DETECTED"
        print(f"\n{state_label}")
        print(f"   Status saved to {STATUS_PATH}")

        if not logged_in:
            sys.exit(2)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
