#!/usr/bin/env python3
"""E2E smoke test for doubao Web AI adapter.
Requires Playwright browser and a logged-in persistent profile.
"""

import asyncio
from backend.skills.external_ai_web.web_ai_skill import WebAISkill


async def main():
    result = await WebAISkill().execute(
        "请用一句话回答：local-ai-orchestrator 的目标是什么？",
        {"provider": "doubao", "headless": False, "max_followups": 1},
    )
    print(result.to_dict())
    if not result.success:
        print("FAILED_OR_NEEDS_LOGIN_OR_SELECTOR_FALLBACK")
    else:
        print("OK")


if __name__ == "__main__":
    asyncio.run(main())
