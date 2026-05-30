from backend.llm.base import LLMProvider, LLMMessage

DEFAULT_CAPS = [
    "read_files",
    "write_files",
    "run_shell",
    "install_dependencies",
    "operate_browser",
    "take_screenshots",
    "ask_external_ai",
    "modify_code",
    "autonomous_retry",
    "autonomous_repair",
]


class DynamicPreflightAnalyzer:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def analyze(self, user_input: str, goal_contract: dict | None = None) -> dict:
        prompt = f"""根据任务和 Goal Contract 生成全自主授权 preflight JSON。字段：required_capabilities, required_resources, recommended_external_ai, preflight_questions。\n任务：{user_input}\nGoal Contract：{goal_contract}"""
        try:
            data = await self.llm.chat_json(
                [LLMMessage(role="user", content=prompt)], temperature=0.2
            )
        except Exception:
            data = {}
        return {
            "required_capabilities": data.get("required_capabilities") or DEFAULT_CAPS,
            "required_resources": data.get("required_resources")
            or [
                "project_path",
                "browser_profiles",
                "external_ai",
                "user_preferences",
                "protected_paths",
            ],
            "recommended_external_ai": data.get("recommended_external_ai")
            or ["ChatGPT", "Claude", "Gemini", "Codex"],
            "preflight_questions": data.get("preflight_questions")
            or [
                "项目路径是什么？",
                "允许修改文件和运行命令吗？",
                "哪些外部 AI 已登录？",
                "有哪些不能动的文件？",
                "目标偏好和风格重点是什么？",
            ],
        }
