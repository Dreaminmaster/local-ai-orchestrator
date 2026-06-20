"""Check external AI answer quality before treating it as a valid response."""

from __future__ import annotations

LOW_QUALITY_PATTERNS = {
    "empty_or_short": ["", "wrapping", "typing", "thinking..."],
    "login_page": [
        "login",
        "sign in",
        "log in",
        "auth",
        "register",
        "create account",
        "登录",
        "注册",
        "继续使用",
    ],
    "captcha": [
        "captcha",
        "verify you are human",
        "human verification",
        "验证码",
        "人机验证",
        "安全验证",
        "请验证你是真人",
    ],
    "error_page": [
        "something went wrong",
        "try again",
        "error occurred",
        "sorry",
        "unavailable",
        "无法处理",
        "出错了",
        "稍后再试",
    ],
    "rate_limit": [
        "rate limit",
        "too many requests",
        "token limit",
        "message limit",
        "conversation limit",
        "quota",
        "额度",
        "次数",
    ],
    "network_error": [
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
    ],
    "not_loaded": ["loading", "please wait", "connecting", "initializing", "加载中"],
}


class AnswerQualityChecker:
    LOW_MIN_CHARS = 20

    def check(
        self,
        answer: str,
        *,
        reliable_answer: bool = True,
        warning_text: str = "",
        warning_class: str = "",
    ) -> dict:
        answer = (answer or "").strip()
        result = {
            "quality": "PASS",
            "issues": [],
            "reliable": True,
        }
        if not answer or len(answer) < self.LOW_MIN_CHARS:
            result["quality"] = "FAIL"
            result["issues"].append("empty_or_short")
            result["reliable"] = False
            return result

        lower = answer.lower()
        for category, patterns in LOW_QUALITY_PATTERNS.items():
            if any(p and p in lower for p in patterns):
                result["issues"].append(category)

        if not reliable_answer:
            result["quality"] = "FAIL"
            result["issues"].append("unreliable_answer_source")
            result["reliable"] = False
            return result

        warning_class = warning_class or (
            "non_blocking_warning" if warning_text else ""
        )
        result["warning_text"] = warning_text
        result["warning_class"] = warning_class

        if warning_class == "non_blocking_warning":
            result["quality"] = "PASS_WITH_WARNING"
            result["issues"] = [
                issue for issue in result["issues"] if issue != "error_page"
            ]
            result["reliable"] = True
            return result

        if result["issues"]:
            result["quality"] = "PARTIAL"
            result["reliable"] = False

        return result
