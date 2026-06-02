import unittest

from backend.skills.external_ai_web.answer_extractor import AnswerExtractor
from backend.skills.external_ai_web.answer_quality_check import AnswerQualityChecker


PROMPT = "请给一个简短、可执行的建议：当本地 Agent 不确定修复方案时，应该如何安全地使用外部 AI？ [REDACTED:generic_api_key_env]"

CLAUDE_PAGE_SHELL = """
Products
Cowork
Code
Low-poly 3D 冰箱互动网页原型
Your first chat with Claude
GO
Genius One
What shall we think through?
请给一个简短、可执行的建议：当本地 Agent 不确定修复方案时，应该如何安全地使用外部 AI？ [REDACTED:generic_api_key_env]
Sonnet 4.6 Medium
New
Create files and artifacts
Claude can do more than answer questions. Ask it to build interactive web apps, write documents, generate spreadsheets and presentations, or create visuals in a dedicated window alongside your chat.
It's all included on your free plan.
Try it out
Pricing Analysis
Spreadsheet · XLSX
Market Research
Document · PDF
Weekly Metrics Review
Presentation · PPTX
Food Truck Business Plan
Document · DOCX
Dialog
"""

CLAUDE_REAL_ANSWER_WITH_VERIFICATION_WORD = """
Check frontend design skill
Check frontend design skill
可执行建议：五步安全调用外部 AI
核心原则：把外部 AI 当成一个不受信任的第三方顾问——只给它需要的信息，不盲信它的答案。
五步流程
① 脱敏上下文 — 在发出任何请求前，自动替换/删除：API key、数据库凭证、真实路径、用户 PII、内部域名。
② 缩小问题范围 — 只提取最小可复现片段，同时把问题描述清楚：报错信息 + 期望行为。
③ 调用外部 AI — prompt 要结构化，明确约束，限制 max_tokens 防止过度生成。
④ 沙箱验证方案 — 把返回的修复代码放进隔离环境跑测试，不要直接合并。
⑤ 记录 & 审计 — 把每次调用的 request-id、脱敏后的 prompt、返回内容、采纳/拒绝决策存档。
"""


class _FakeElement:
    def __init__(self, text: str):
        self.text = text

    async def inner_text(self, timeout=0):
        return self.text


class _FakeLocator:
    def __init__(self, texts: list[str]):
        self.texts = texts
        self.index = 0

    async def count(self):
        return len(self.texts)

    def nth(self, index: int):
        loc = _FakeLocator(self.texts)
        loc.index = index
        return loc

    async def inner_text(self, timeout=0):
        if not self.texts:
            return ""
        return self.texts[self.index]


class _FakePage:
    def __init__(self, by_selector: dict[str, list[str]], body: str):
        self.by_selector = by_selector
        self.body = body

    def locator(self, selector: str):
        if selector == "body":
            return _FakeLocator([self.body])
        return _FakeLocator(self.by_selector.get(selector, []))


class ClaudeAnswerExtractorEvidenceTest(unittest.IsolatedAsyncioTestCase):
    async def test_evidence_page_shell_is_reliable_failure_not_pass(self):
        extractor = AnswerExtractor()

        answer = await extractor.latest(_FakePage({}, CLAUDE_PAGE_SHELL), "claude", PROMPT)

        self.assertIn("What shall we think through", answer)
        self.assertEqual(extractor.used_selector, "body_fallback")
        self.assertTrue(extractor.used_body_fallback)
        self.assertEqual(extractor.error_reason, "claude_reliable_answer_not_found")
        self.assertTrue(extractor.raw_body_fallback)
        fallback = [
            item for item in extractor.candidate_selectors
            if item.get("selector") == "body_fallback"
        ]
        self.assertTrue(fallback)
        self.assertFalse(fallback[-1]["chosen"])

    async def test_prefers_last_main_assistant_like_block(self):
        answer = (
            "建议：外部 AI 只能作为顾问，本地 Agent 保留最终决策权。\n"
            "1. 先脱敏 prompt、日志和配置。\n"
            "2. 只发送最小必要上下文。\n"
            "3. 把外部建议保存为 evidence，并由本地测试验证后再采用。"
        )
        page = _FakePage(
            {
                "main [class*='message']": [
                    PROMPT,
                    "New chat\nRecents\nProjects\nUpgrade",
                    answer,
                ]
            },
            "New chat\nRecents\nProjects\nUpgrade\n" + PROMPT + "\n" + answer,
        )
        extractor = AnswerExtractor()

        extracted = await extractor.latest(page, "claude", PROMPT)

        self.assertEqual(extracted, answer)
        self.assertEqual(extractor.used_selector, "main [class*='message']")
        self.assertFalse(extractor.used_body_fallback)
        chosen = [item for item in extractor.candidate_selectors if item.get("chosen")]
        self.assertEqual(len(chosen), 1)
        self.assertGreaterEqual(chosen[0]["score"], 35)

    async def test_chinese_verification_word_is_not_captcha_by_itself(self):
        quality = AnswerQualityChecker().check(CLAUDE_REAL_ANSWER_WITH_VERIFICATION_WORD)

        self.assertNotIn("captcha", quality["issues"])

    async def test_page_error_banner_is_not_assistant_answer(self):
        page = _FakePage(
            {
                "main [class*='font-claude']": [
                    "Network error. Unable to connect. Reconnecting...",
                ]
            },
            "Network error. Unable to connect. Reconnecting...",
        )
        extractor = AnswerExtractor()

        answer = await extractor.latest(page, "claude", PROMPT)

        self.assertEqual(extractor.used_selector, "body_fallback")
        self.assertTrue(extractor.used_body_fallback)
        self.assertIn("Network error", answer)
        rejected = [
            item for item in extractor.candidate_selectors
            if item.get("rejected_reason") == "page_error_banner"
        ]
        self.assertTrue(rejected)


if __name__ == "__main__":
    unittest.main()
