"""Pending External AI action APIs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from backend.local_model.step_state_store import StepStateStore
from backend.skills.external_ai_web.pending_action import pending_external_ai_store
from backend.skills.external_ai_web.provider_status import (
    ProviderState,
    normalize_provider,
)
from backend.skills.external_ai_web.web_ai_skill import WebAISkill
from backend.skills.external_ai_web.workspace_manager import workspace_manager

router = APIRouter(tags=["external-ai-actions"])


READY_STATES = {ProviderState.READY, ProviderState.PASS, ProviderState.PARTIAL}
NEEDS_USER_STATES = {
    ProviderState.NEED_LOGIN,
    ProviderState.NEED_USER_INTERVENTION,
    ProviderState.STALE_CONVERSATION,
    ProviderState.PAGE_NETWORK_ERROR,
    ProviderState.RETRYABLE_PAGE_ERROR,
}


@router.get("/external-ai/pending")
async def list_pending_external_ai():
    return {"pending": pending_external_ai_store.list_pending()}


@router.post("/external-ai/{task_id}/resume")
async def resume_pending_external_ai(task_id: str):
    pending = pending_external_ai_store.load(task_id)
    if not pending:
        return {"task_id": task_id, "error": "pending_external_ai_not_found"}

    provider = normalize_provider(pending.get("provider", "claude"))
    status = await workspace_manager.get_workspace_status(provider)
    if status.state in NEEDS_USER_STATES or status.state not in READY_STATES:
        return {
            "task_id": task_id,
            "provider": provider,
            "still_needs_user": True,
            "provider_status": status.state.value,
            "failure_reason": pending.get("failure_reason")
            or status.state.value.lower(),
            "suggested_user_action": pending.get("suggested_user_action")
            or "Open the provider workspace, handle login/verification, then resume.",
            "can_resume": True,
            "workspace_status": status.to_dict(),
            "event": {
                "type": "external_ai_resume_still_needs_user",
                "data": {
                    "task_id": task_id,
                    "provider": provider,
                    "status": status.state.value,
                },
            },
        }

    context = dict(pending.get("context") or {})
    context.update(
        {
            "task_id": task_id,
            "provider": provider,
            "target": provider,
            "prompt": pending.get("redacted_prompt")
            or pending.get("original_prompt", ""),
            "reuse_workspace": True,
            "resuming_pending_external_ai": True,
        }
    )
    result = await WebAISkill().execute(
        pending.get("redacted_prompt") or pending.get("original_prompt", ""),
        context,
    )
    result_dict = result.to_dict()
    store = StepStateStore()
    state = store.load(task_id)
    if state:
        state.last_tool_results.append(result_dict)
        state.next_actions.append(
            {
                "type": "external_ai_resume_result",
                "provider": provider,
                "success": result.success,
                "created_at": datetime.now().isoformat(),
            }
        )
        store.save(state)

    out_path = Path("runtime/tasks") / task_id / "pending_external_ai_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        __import__("json").dumps(result_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if result.success:
        pending_external_ai_store.clear(task_id)
        event_type = "external_ai_resume_success"
    elif result.metadata.get("need_user_intervention"):
        event_type = "external_ai_resume_still_needs_user"
    else:
        event_type = "external_ai_resume_failed"
    return {
        "task_id": task_id,
        "provider": provider,
        "still_needs_user": bool(result.metadata.get("need_user_intervention")),
        "success": result.success,
        "result": result_dict,
        "evidence": result.evidence,
        "failure_reason": result.metadata.get("failure_reason") or result.error or "",
        "resume_payload": (
            {"task_id": task_id, "resume_from_task_id": task_id}
            if result.success
            else None
        ),
        "result_path": str(out_path),
        "event": {
            "type": event_type,
            "data": {"task_id": task_id, "provider": provider},
        },
    }
