import json, re
class ActionableExtractor:
    def extract_json(self, text: str) -> dict:
        try: return json.loads(text)
        except Exception: pass
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
        return {"raw": text, "css_suggestions": [], "problems": []}

    def to_tasks(self, review: dict) -> list[str]:
        return list(review.get("css_suggestions") or review.get("improvements") or [])
