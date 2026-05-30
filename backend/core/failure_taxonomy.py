class FailureTaxonomy:
    KEYWORDS={
        'json_parse_failed':['json parse','failed to parse json','invalid json'],
        'local_model_uncertain':['uncertain','不确定','无法判断'],
        'context_overflow':['context','too long','maximum context','上下文'],
        'tool_result_too_long':['result too long','output too long','日志太长'],
        'external_ai_needed':['escalate','external ai needed','需要外部 ai'],
        'goal_unclear':['目标不清','unclear goal','ambiguous','clarify'],
        'authorization_missing':['not granted','permission','authorization','requires confirmation','未授权'],
        'resource_missing':['not found','missing','no such file','缺少','路径不存在'],
        'selector_failed':['selector','locator','element not found','timeout waiting','无法定位'],
        'external_ai_failed':['api key','external ai','login required','rate limit','外部 ai'],
        'visual_quality_failed':['visual','low score','not premium','不够高级','视觉不达标'],
        'code_failed':['traceback','syntaxerror','exception','test failed','build failed','报错'],
        'network_failure':['timeout','connection','network','dns'],
        'permission_failure':['permission denied','unauthorized','forbidden'],
    }
    def classify(self, text: str) -> str:
        lower=(text or '').lower()
        for k,words in self.KEYWORDS.items():
            if any(w.lower() in lower for w in words): return k
        return 'tool_failure'
