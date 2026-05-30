from __future__ import annotations
from backend.schemas.clarification_session import (
    ClarificationSession,
    ClarificationQuestion,
    ClarificationAnswer,
)
from backend.llm.base import LLMProvider, LLMMessage
from backend.evidence.board import EvidenceBoard


class ClarificationSessionStore:
    def __init__(self):
        self.sessions: dict[str, ClarificationSession] = {}

    def create(self, session: ClarificationSession) -> ClarificationSession:
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str) -> ClarificationSession | None:
        return self.sessions.get(session_id)

    def update(self, session: ClarificationSession) -> ClarificationSession:
        self.sessions[session.id] = session
        return session


clarification_store = ClarificationSessionStore()


class ClarificationSessionService:
    def __init__(self, llm: LLMProvider, evidence_board: EvidenceBoard | None = None):
        self.llm = llm
        self.evidence = evidence_board or EvidenceBoard()

    async def prepare(self, user_input: str, goal_mode: str) -> dict:
        if goal_mode != "clarify_first":
            return {"needs_clarification": False}
        prompt = f"""针对用户任务提出开始前必须澄清的问题，最多5个。输出 JSON：{{"questions":[{{"question":"...","reason":"...","required":true}}]}}\n任务：{user_input}"""
        try:
            data = await self.llm.chat_json(
                [LLMMessage(role="user", content=prompt)], temperature=0.2
            )
            raw_questions = data.get("questions", [])
        except Exception:
            raw_questions = [
                {
                    "question": "请确认最终目标是什么？",
                    "reason": "避免方向错误",
                    "required": True,
                },
                {
                    "question": "有哪些不能修改的范围或约束？",
                    "reason": "避免越权操作",
                    "required": False,
                },
                {
                    "question": "成功标准是什么？",
                    "reason": "用于后续验证",
                    "required": True,
                },
            ]
        questions = [ClarificationQuestion(**q) for q in raw_questions[:5]]
        session = clarification_store.create(
            ClarificationSession(
                original_input=user_input,
                goal_mode="clarify_first",
                questions=questions,
            )
        )
        for q in questions:
            self.evidence.save(
                session.id,
                None,
                "clarification_question",
                "intent_clarifier",
                q.question,
                q.reason,
            )
        return {
            "needs_clarification": True,
            "clarification_session": session.model_dump(),
        }

    def answer(self, session_id: str, answers: list[dict]) -> ClarificationSession:
        session = clarification_store.get(session_id)
        if not session:
            raise ValueError(f"Clarification session not found: {session_id}")
        session.answers = [ClarificationAnswer(**a) for a in answers]
        session.status = "answered"
        clarification_store.update(session)
        for a in session.answers:
            self.evidence.save(
                session.id,
                None,
                "clarification_answer",
                "user",
                a.answer,
                f"Answer to {a.question_id}",
            )
        return session

    def summary(self, session: ClarificationSession) -> str:
        qmap = {q.id: q.question for q in session.questions}
        return "\n".join(
            [
                f"Q: {qmap.get(a.question_id,a.question_id)}\nA: {a.answer}"
                for a in session.answers
            ]
        )
