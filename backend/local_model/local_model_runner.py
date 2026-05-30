from backend.local_model.retry_policy import LocalModelRetryPolicy
from backend.local_model.json_repair import JSONRepairParser
from backend.local_model.external_ai_escalation import ExternalAIEscalationRouter

class LocalModelRunner:
    """Unified local-model JSON caller: prompt -> LLM -> repair -> retry -> escalation/fallback."""
    def __init__(self, llm, retry_policy=None, json_parser=None, escalation_router=None):
        self.llm = llm
        self.retry_policy = retry_policy or LocalModelRetryPolicy()
        self.json_parser = json_parser or JSONRepairParser()
        self.escalation_router = escalation_router or ExternalAIEscalationRouter()

    async def run_json(self, build_prompt, context: dict, output_schema: dict, fallback: dict, escalation_reason: str | None=None):
        result = await self.retry_policy.run_with_retry(
            llm=self.llm,
            build_prompt=build_prompt,
            parser=self.json_parser,
            context=context,
            output_schema=output_schema,
            fallback=fallback,
            escalation_router=self.escalation_router,
        )
        if result.get('needs_escalation') and escalation_reason:
            result['escalation_reason'] = escalation_reason
        return result
