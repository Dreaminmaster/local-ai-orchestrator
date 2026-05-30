#!/usr/bin/env python3
"""E2E demo: desktop visual observe/click verification path."""

import asyncio
from backend.skills.desktop_visual.desktop_visual_skill import DesktopVisualSkill


async def main():
    result = await DesktopVisualSkill().execute(
        "observe screen",
        {"action": "observe_screen", "save_as": "runtime/evidence/desktop_demo.png"},
    )
    print(result.to_dict())


if __name__ == "__main__":
    asyncio.run(main())
