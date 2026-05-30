from .schemas import ConfirmationRequest
class ConfirmationQueue:
    def __init__(self): self.items: dict[str, ConfirmationRequest] = {}
    def add(self, req: ConfirmationRequest) -> ConfirmationRequest:
        self.items[req.id]=req; return req
    def list(self): return list(self.items.values())
    def decide(self, req_id: str, approved: bool):
        req=self.items[req_id]; req.status="approved" if approved else "rejected"; return req
