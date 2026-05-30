import json, re
class JSONRepairParser:
    def parse(self, text: str, fallback: dict | None = None) -> dict:
        fallback = fallback or {}
        if not text: return fallback
        try: return json.loads(text)
        except Exception: pass
        cleaned = text.strip().replace('```json','').replace('```','').strip()
        try: return json.loads(cleaned)
        except Exception: pass
        extracted = self._extract_json_object(cleaned)
        if extracted:
            for candidate in [extracted, self._repair_common_errors(extracted)]:
                try: return json.loads(candidate)
                except Exception: pass
        return fallback
    def _extract_json_object(self, text: str) -> str | None:
        start=text.find('{'); end=text.rfind('}')
        if start >= 0 and end > start: return text[start:end+1]
        return None
    def _repair_common_errors(self, text: str) -> str:
        text=text.replace('，', ',').replace('：', ':').replace('“','"').replace('”','"')
        text=re.sub(r'//.*','',text)
        text=re.sub(r',\s*([}\]])', r'\1', text)
        return text
