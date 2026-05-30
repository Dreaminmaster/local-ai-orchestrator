class ToolResultSummarizer:
    def summarize(self, skill_name: str, result: dict) -> dict:
        raw = str(result.get('result','')) + '\n' + str(result.get('error',''))
        if skill_name == 'shell': return self._summarize_shell(raw, result)
        if skill_name == 'browser': return self._summarize_browser(raw, result)
        if skill_name in ['external_ai','web_ai']: return self._summarize_external_ai(raw, result)
        return {'skill': skill_name, 'summary': raw[:1500], 'success': result.get('success', False), 'evidence': result.get('evidence', []), 'metadata': result.get('metadata', {})}
    def _summarize_shell(self, raw: str, result: dict) -> dict:
        lines=raw.splitlines(); important=[l for l in lines if any(k in l.lower() for k in ['error','failed','traceback','exception','warning','listening','localhost'])]
        return {'skill':'shell','summary':'\n'.join(important[-30:]) or '\n'.join(lines[-30:]), 'success': result.get('success', False), 'evidence': result.get('evidence', []), 'metadata': result.get('metadata', {})}
    def _summarize_browser(self, raw: str, result: dict) -> dict:
        return {'skill':'browser','summary':raw[:2000], 'success': result.get('success', False), 'url': result.get('metadata',{}).get('url'), 'evidence': result.get('evidence', [])}
    def _summarize_external_ai(self, raw: str, result: dict) -> dict:
        return {'skill': result.get('skill','external_ai'), 'summary': raw[:2500], 'success': result.get('success', False), 'provider': result.get('metadata',{}).get('provider'), 'evidence': result.get('evidence', [])}
