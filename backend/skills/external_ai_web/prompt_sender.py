from .selectors import SELECTORS


class PromptSender:
    async def send(
        self, page, provider: str, prompt: str, attachments: list[str] | None = None
    ):
        sel = SELECTORS.get(provider, SELECTORS["chatgpt"])["input"]
        locator = page.locator(sel).last
        await locator.wait_for(timeout=30000)
        await locator.click()
        await locator.fill(prompt)
        send_sel = SELECTORS.get(provider, SELECTORS["chatgpt"])["send"]
        try:
            await page.locator(send_sel).last.click(timeout=5000)
        except Exception:
            await page.keyboard.press("Enter")
