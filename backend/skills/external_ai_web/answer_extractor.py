import asyncio
from .selectors import SELECTORS


class AnswerExtractor:
    async def wait_complete(self, page, timeout: int = 180) -> bool:
        last = ""
        stable = 0
        for _ in range(timeout):
            try:
                text = await page.locator("body").inner_text(timeout=5000)
            except Exception:
                await asyncio.sleep(2)
                continue
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
        try:
            loc = page.locator(sel)
            count = await loc.count()
            if count:
                return await loc.nth(count - 1).inner_text(timeout=10000)
        except Exception:
            pass
        # body_marker fallback: use marker text to locate last answer block
        marker = SELECTORS.get(provider, {}).get("body_marker")
        if marker:
            try:
                body = await page.locator("body").inner_text(timeout=10000)
                idx = body.rfind(marker)
                if idx > 0:
                    return body[idx:]
            except Exception:
                pass
        try:
            return (await page.locator("body").inner_text(timeout=10000))[-4000:]
        except Exception:
            return ""
