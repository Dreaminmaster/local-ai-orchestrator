#!/usr/bin/env python3
"""E2E demo: ask external AI through web workspace."""

import asyncio
from backend.skills.external_ai_web.web_ai_skill import WebAISkill


async def main():
    result = await WebAISkill().execute(
        "请简要说明什么是自监督 AI Agent。", {"provider": "chatgpt", "headless": False}
    )
    print(result.to_dict())


if __name__ == "__main__":
    asyncio.run(main())
