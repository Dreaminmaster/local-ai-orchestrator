from backend.llm.base import LLMProvider, LLMMessage

class IntentClarifier:
    def __init__(self, llm: LLMProvider): self.llm=llm
    async def clarify(self, user_input: str, goal_mode: str) -> dict:
        if goal_mode == "autonomous":
            return {"questions": [], "summary": "自主创意模式：AI 根据上下文和偏好补全目标。"}
        prompt=f"请针对这个任务提出最多5个开始前必须澄清的问题，不要执行：{user_input}"
        try:
            resp=await self.llm.chat([LLMMessage(role='user', content=prompt)], temperature=0.2, max_tokens=800)
            questions=[x.strip('- 0123456789.、') for x in resp.content.splitlines() if x.strip()]
            return {"questions": questions[:5], "summary": resp.content}
        except Exception as e:
            return {"questions": ["请确认最终目标、范围、成功标准和限制。"], "summary": str(e)}
