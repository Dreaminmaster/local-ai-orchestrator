class FailureTaxonomy:
    KEYWORDS={
        'login_failure':['login','sign in','登录'],
        'network_failure':['timeout','connection','network'],
        'code_failure':['traceback','syntaxerror','exception','failed'],
        'permission_failure':['permission denied','unauthorized','forbidden'],
        'quality_failure':['not good','low score','不达标'],
    }
    def classify(self, text: str) -> str:
        lower=(text or '').lower()
        for k,words in self.KEYWORDS.items():
            if any(w in lower for w in words): return k
        return 'tool_failure'
