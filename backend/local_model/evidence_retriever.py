class EvidenceRetriever:
    def __init__(self, evidence_board): self.evidence_board = evidence_board
    def retrieve_for_step(self, task_id: str, current_step: dict, max_items: int = 8) -> list[dict]:
        all_evidence = self.evidence_board.get_task_evidence(task_id)
        keywords = self._extract_keywords(current_step)
        scored=[]
        for item in all_evidence:
            score=self._score(item, keywords)
            if score>0: scored.append((score,item))
        scored.sort(key=lambda x:x[0], reverse=True)
        return [item for _,item in scored[:max_items]] or all_evidence[-max_items:]
    def _extract_keywords(self, step: dict) -> list[str]:
        text=str(step).lower(); keys=[]
        for k in ['error','screenshot','diff','terminal','visual','external_ai','browser','code','file','shell','goal','authorization']:
            if k in text: keys.append(k)
        return keys
    def _score(self, evidence: dict, keywords: list[str]) -> int:
        text=str(evidence).lower(); return sum(1 for k in keywords if k in text)
