class FailureTaxonomy:
    KEYWORDS={
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
