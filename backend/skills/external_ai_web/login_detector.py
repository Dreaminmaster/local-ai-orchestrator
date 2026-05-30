class LoginDetector:
    async def detect(self, page, provider: str) -> bool:
        url = page.url.lower()
        try:
            text = (await page.locator("body").inner_text(timeout=5000)).lower()
        except Exception:
            text = ""
        login_words = ["login", "sign in", "log in", "登录", "注册", "继续使用"]
        if any(w in url for w in ["login", "signin", "auth"]):
            return False
        if any(w in text[:3000] for w in login_words):
            count = await page.locator("textarea, [contenteditable='true']").count()
            return count > 0 and "登录" not in text[:1000]
        return await page.locator("textarea, [contenteditable='true']").count() > 0
