import asyncio
from .selectors import SELECTORS


class AnswerExtractor:
    async def wait_complete(self, page, timeout: int = 180) -> bool:
        last = ""
        stable = 0
        for _ in range(timeout):
            text = await page.locator("body").inner_text(timeout=5000)
            if text == last:
                stable += 1
                if stable >= 3:
                    return True
            else:
                stable = 0
                last = text
            await asyncio.sleep(1)
        return False

    async def latest(self, page, provider: str) -> str:
        sel = SELECTORS.get(provider, SELECTORS["chatgpt"])["messages"]
        loc = page.locator(sel)
        count = await loc.count()
        if count:
            return await loc.nth(count - 1).inner_text(timeout=10000)
        return (await page.locator("body").inner_text(timeout=10000))[-4000:]
