from backend.llm.base import LLMMessage

class LocalModelRetryPolicy:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def run_with_retry(self, llm, build_prompt, parser, context, output_schema, fallback, escalation_router=None):
        attempts=[]
        for attempt in range(self.max_retries):
            prompt=build_prompt(context, output_schema, attempt=attempt)
            try:
                raw=await llm.chat([LLMMessage(role='user', content=prompt)], temperature=0.2, json_mode=True)
                parsed=parser.parse(raw.content if hasattr(raw,'content') else str(raw))
                if parsed:
                    return parsed
                attempts.append(raw)
            except Exception as exc:
                attempts.append(exc)
            context=self._shrink_context(context)
        if escalation_router and escalation_router.should_escalate('json_parse_failed', {'json_parse_failures':len(attempts)}):
            fallback = dict(fallback)
            fallback.update({'needs_escalation': True, 'reason':'Local model failed to produce valid JSON or was unreachable', 'attempts':[str(x) for x in attempts]})
            return fallback
        return fallback

    def _shrink_context(self, context: dict) -> dict:
        c=dict(context)
        c['relevant_evidence']=c.get('relevant_evidence',[])[:2]
        c['state_summary']=c.get('state_summary','')[:800]
        return c
