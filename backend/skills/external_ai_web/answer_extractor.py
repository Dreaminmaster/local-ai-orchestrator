import asyncio
from datetime import datetime
from .selectors import SELECTORS


class AnswerExtractor:
    NAV_HINTS = [
        "new chat",
        "chats",
        "projects",
        "artifacts",
        "customize",
        "recents",
        "free plan",
        "upgrade",
        "get apps and extensions",
        "how can i help you today",
        "this conversation could not be found",
        "conversation not found",
        "products",
        "cowork",
        "code",
        "games",
        "apps and websites",
        "create files and artifacts",
        "your first chat with claude",
        "what shall we think through",
        "try it out",
        "pricing analysis",
        "market research",
        "weekly metrics review",
        "food truck business plan",
        "settings",
        "project",
        "projects",
        "upgrade",
        "recents",
        "new",
    ]
    GENERATION_HINTS = [
        "thinking",
        "thinking...",
        "正在思考",
        "stop generating",
        "停止回答",
        "typing",
    ]
    PAGE_ERROR_HINTS = [
        "network error",
        "connection lost",
        "connection failed",
        "unable to connect",
        "request timed out",
        "reconnecting",
        "网络错误",
        "无法连接",
        "连接失败",
        "请求超时",
    ]
    NON_BLOCKING_WARNING_HINTS = [
        "is currently unavailable",
        "model is currently unavailable",
        "learn more",
    ]

    def __init__(self):
        self.used_selector = ""
        self.used_body_fallback = False
        self.candidate_selectors: list[dict] = []
        self.raw_body_fallback = ""
        self.error_reason = ""
        self.warning_text = ""
        self.warning_class = ""
        self.answer_timestamp = ""

    async def wait_complete(self, page, timeout: int = 180) -> bool:
        last = ""
        stable = 0
        for _ in range(timeout):
            text = await self._candidate_text_snapshot(page)
            lower = text.lower()
            if any(token in lower for token in ["thinking", "正在思考", "停止回答", "stop generating"]):
                stable = 0
                await asyncio.sleep(1)
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

    async def latest(self, page, provider: str, exclude_text: str = "") -> str:
        self.used_selector = ""
        self.used_body_fallback = False
        self.candidate_selectors = []
        self.raw_body_fallback = ""
        self.error_reason = ""
        self.warning_text = ""
        self.warning_class = ""
        self.answer_timestamp = ""
        if provider == "claude":
            return await self._latest_claude(page, exclude_text)
        selectors = self._selectors(provider)
        best_text = ""
        best_selector = ""
        for sel in selectors:
            loc = page.locator(sel)
            try:
                count = await loc.count()
            except Exception as exc:
                self.candidate_selectors.append({"selector": sel, "error": str(exc)})
                continue
            candidates = []
            for i in range(max(0, count - 8), count):
                try:
                    text = (await loc.nth(i).inner_text(timeout=3000)).strip()
                except Exception:
                    continue
                cleaned = self._clean(text)
                score, rejected = self._score_candidate(
                    cleaned, sel, provider, exclude_text, in_main=("main" in sel), ordinal=i, total=count
                )
                if not rejected:
                    candidates.append(cleaned)
                self.candidate_selectors.append(
                    {
                        "selector": sel,
                        "candidate_count": count,
                        "text_preview": cleaned[:220],
                        "score": score,
                        "rejected_reason": rejected,
                        "chosen": False,
                    }
                )
            self.candidate_selectors.append(
                {"selector": sel, "count": count, "usable": len(candidates)}
            )
            if candidates:
                best_text = candidates[-1]
                best_selector = sel
                break
        if best_text:
            self.used_selector = best_selector
            self.answer_timestamp = datetime.now().isoformat()
            await self._capture_page_warning(page, reliable_answer=True)
            return best_text

        body = (await page.locator("body").inner_text(timeout=10000))[-4000:]
        parsed = self._parse_provider_body(provider, body)
        if parsed:
            self.used_body_fallback = False
            self.used_selector = f"body_marker:{provider}"
            self.answer_timestamp = datetime.now().isoformat()
            await self._capture_page_warning(page, reliable_answer=False)
            return parsed
        self.used_body_fallback = True
        self.used_selector = "body_fallback"
        self.raw_body_fallback = body
        await self._capture_page_warning(page, reliable_answer=False)
        return self._clean(body)

    async def _latest_claude(self, page, exclude_text: str = "") -> str:
        selectors = self._selectors("claude")
        best: dict | None = None
        for sel in selectors:
            loc = page.locator(sel)
            try:
                count = await loc.count()
            except Exception as exc:
                self.candidate_selectors.append(
                    {
                        "selector": sel,
                        "candidate_count": 0,
                        "text_preview": "",
                        "score": 0,
                        "rejected_reason": str(exc),
                        "chosen": False,
                    }
                )
                continue
            for i in range(max(0, count - 20), count):
                try:
                    text = (await loc.nth(i).inner_text(timeout=2000)).strip()
                except Exception as exc:
                    self.candidate_selectors.append(
                        {
                            "selector": sel,
                            "candidate_count": count,
                            "text_preview": "",
                            "score": 0,
                            "rejected_reason": f"inner_text_failed: {exc}",
                            "chosen": False,
                        }
                    )
                    continue
                cleaned = self._clean(text)
                score, rejected = self._score_candidate(
                    cleaned,
                    sel,
                    "claude",
                    exclude_text,
                    in_main=sel.startswith("main"),
                    ordinal=i,
                    total=count,
                )
                record = {
                    "selector": sel,
                    "candidate_count": count,
                    "text_preview": cleaned[:220],
                    "score": score,
                    "rejected_reason": rejected,
                    "chosen": False,
                }
                self.candidate_selectors.append(record)
                if not rejected and (best is None or score >= best["score"]):
                    best = {"text": cleaned, "selector": sel, "score": score, "record": record}

        if best:
            best["record"]["chosen"] = True
            self.used_selector = best["selector"]
            self.answer_timestamp = datetime.now().isoformat()
            await self._capture_page_warning(page, reliable_answer=True)
            return best["text"]

        body = (await page.locator("body").inner_text(timeout=10000))[-6000:]
        parsed = self._parse_provider_body("claude", body)
        if parsed:
            self.used_body_fallback = False
            self.used_selector = "body_marker:claude"
            self.answer_timestamp = datetime.now().isoformat()
            self.candidate_selectors.append(
                {
                    "selector": "body_marker:claude",
                    "candidate_count": 1,
                    "text_preview": parsed[:220],
                    "score": 55,
                    "rejected_reason": "",
                    "chosen": True,
                }
            )
            await self._capture_page_warning(page, reliable_answer=False)
            return parsed

        self.used_body_fallback = True
        self.used_selector = "body_fallback"
        self.raw_body_fallback = body
        self.error_reason = "claude_reliable_answer_not_found"
        await self._capture_page_warning(page, reliable_answer=False)
        self.candidate_selectors.append(
            {
                "selector": "body_fallback",
                "candidate_count": 1,
                "text_preview": self._clean(body)[:220],
                "score": 0,
                "rejected_reason": self.error_reason,
                "chosen": False,
            }
        )
        return self._clean(body)

    async def _candidate_text_snapshot(self, page) -> str:
        try:
            return await page.locator("main").inner_text(timeout=3000)
        except Exception:
            return await page.locator("body").inner_text(timeout=5000)

    def _selectors(self, provider: str) -> list[str]:
        base = SELECTORS.get(provider, SELECTORS["chatgpt"])["messages"]
        selectors = [s.strip() for s in base.split(",") if s.strip()]
        if provider == "claude":
            selectors = [
                "main [data-testid*='message']",
                "main [data-testid*='conversation']",
                "main article",
                "main [role='article']",
                "main [class*='message']",
                "main [class*='font-claude']",
                "[class*='message']",
                "[class*='font-claude']",
                "[data-testid*='message']",
                "[data-testid*='conversation']",
                ".font-claude-message",
            ] + selectors
        elif provider == "chatgpt":
            selectors = [
                "[data-message-author-role='assistant']",
                "[data-testid*='conversation-turn'] [data-message-author-role='assistant']",
                ".markdown",
                "main article",
                "main [role='article']",
            ] + selectors
        return list(dict.fromkeys(selectors))

    def _clean(self, text: str) -> str:
        lines = []
        for line in (text or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if lower in self.NAV_HINTS or any(lower == hint for hint in self.NAV_HINTS):
                continue
            if any(hint == lower for hint in self.GENERATION_HINTS):
                continue
            if len(stripped) <= 2 and not stripped.isalnum():
                continue
            lines.append(stripped)
        return "\n".join(lines).strip()

    def _is_probable_answer(self, text: str, exclude_text: str = "") -> bool:
        if len((text or "").strip()) < 20:
            return False
        if exclude_text and text.strip() == exclude_text.strip():
            return False
        lower = text.lower()
        nav_hits = sum(1 for hint in self.NAV_HINTS if hint in lower)
        if nav_hits >= 3:
            return False
        if "how can i help you today" in lower and len(text) < 500:
            return False
        return True

    def _score_candidate(
        self,
        text: str,
        selector: str,
        provider: str,
        exclude_text: str = "",
        *,
        in_main: bool,
        ordinal: int,
        total: int,
    ) -> tuple[int, str]:
        text = (text or "").strip()
        lower = text.lower()
        if len(text) < 30:
            return 0, "too_short"
        if exclude_text:
            prompt = exclude_text.strip()
            if text == prompt or prompt in text:
                return 0, "contains_user_prompt"
        if any(hint in lower for hint in self.GENERATION_HINTS):
            return 0, "generation_in_progress"
        if any(hint in lower for hint in self.PAGE_ERROR_HINTS):
            return 0, "page_error_banner"
        sidebar_hits = sum(1 for hint in self.NAV_HINTS if hint in lower)
        if sidebar_hits >= 3:
            return 0, "sidebar_or_landing_markers"
        if provider == "claude" and "create files and artifacts" in lower:
            return 0, "claude_artifacts_modal"
        if provider == "claude" and "what shall we think through" in lower:
            return 0, "claude_home_or_composer"
        if lower.count("\n") > 18 and sidebar_hits >= 2:
            return 0, "mixed_page_chrome"

        score = min(len(text), 1400) // 20
        if in_main:
            score += 25
        if "article" in selector or "message" in selector or "font-claude" in selector:
            score += 15
        if total > 0 and ordinal >= total - 3:
            score += 10
        if sidebar_hits:
            score -= sidebar_hits * 8
        if len(text) > 3500:
            score -= 25
        minimum_score = 25 if provider == "claude" and "font-claude" in selector else 35
        if score < minimum_score:
            return score, "low_score"
        return score, ""

    async def _capture_page_warning(self, page, *, reliable_answer: bool) -> None:
        try:
            body = await page.locator("body").inner_text(timeout=3000)
        except Exception:
            return
        lines = []
        for line in body.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if stripped and any(hint in lower for hint in self.NON_BLOCKING_WARNING_HINTS):
                lines.append(stripped)
        self.warning_text = "\n".join(dict.fromkeys(lines))
        if self.warning_text:
            self.warning_class = (
                "non_blocking_warning" if reliable_answer else "blocking_error"
            )

    def _parse_provider_body(self, provider: str, text: str) -> str:
        cleaned = self._clean(text)
        if provider == "claude" and "Claude responded:" in cleaned:
            answer = cleaned.split("Claude responded:", 1)[1]
            stop_markers = [
                "\n2 / 2",
                "\n1 / 1",
                "\nSonnet",
                "\nClaude is AI",
                "\nShare",
            ]
            for marker in stop_markers:
                if marker in answer:
                    answer = answer.split(marker, 1)[0]
            lines = []
            previous = None
            for line in answer.splitlines():
                stripped = line.strip()
                if not stripped or stripped == previous:
                    continue
                previous = stripped
                lines.append(stripped)
            parsed = "\n".join(lines).strip()
            if len(parsed) >= 20:
                return parsed
        return ""
