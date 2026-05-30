from fastapi import APIRouter
from backend.confirmation.queue import confirmation_queue

router = APIRouter(tags=["confirmations"])


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
async def reject(req_id: str):
    return confirmation_queue.decide(req_id, False).__dict__
