from fastapi import APIRouter
from pydantic import BaseModel
from backend.confirmation.queue import confirmation_queue
from backend.confirmation.pending_action_executor import PendingActionExecutor

router = APIRouter(tags=["confirmations"])
executor = PendingActionExecutor()


class RejectBody(BaseModel):
    reason: str = ""


@router.get("/confirmations")
async def list_confirmations():
    return {"items": [x.__dict__ for x in confirmation_queue.list()]}


@router.get("/confirmations/pending")
async def pending_confirmations():
    return {"items": [x.__dict__ for x in confirmation_queue.pending()]}


@router.post("/confirmations/{req_id}/approve")
async def approve(req_id: str):
    return confirmation_queue.decide(req_id, True).__dict__


@router.post("/confirmations/{req_id}/reject")
async def reject(req_id: str, body: RejectBody | None = None):
    reason = body.reason if body else ""
    return confirmation_queue.decide(req_id, False).__dict__ | {"reason": reason}


@router.post("/confirmations/{req_id}/approve-execute")
async def approve_execute(req_id: str):
    """Approve and execute the pending action in-place."""
    return await executor.approve_and_execute(req_id)


@router.post("/confirmations/{req_id}/reject-repair")
async def reject_repair(req_id: str, body: RejectBody):
    """Reject and insert repair steps, then allow resume."""
    return await executor.reject_and_repair(req_id, body.reason)
