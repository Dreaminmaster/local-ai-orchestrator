from fastapi import APIRouter
from backend.confirmation.queue import ConfirmationQueue
router = APIRouter(tags=["confirmations"])
queue = ConfirmationQueue()
@router.get("/confirmations")
async def list_confirmations(): return {"items": [x.__dict__ for x in queue.list()]}
@router.post("/confirmations/{req_id}/approve")
async def approve(req_id: str): return queue.decide(req_id, True).__dict__
@router.post("/confirmations/{req_id}/reject")
async def reject(req_id: str): return queue.decide(req_id, False).__dict__
