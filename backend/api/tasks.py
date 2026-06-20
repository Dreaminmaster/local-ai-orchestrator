"""Tasks API — Create and manage tasks."""

from __future__ import annotations
import asyncio
import hashlib
import json
import uuid
import subprocess
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, StreamingResponse

from backend.core.task_artifact_store import TaskArtifactStore

router = APIRouter(tags=["tasks"])
artifact_store = TaskArtifactStore()
active_real_project_tasks: dict[str, str] = {}


class TaskCreate(BaseModel):
    user_input: str


class RealProjectTaskCreate(BaseModel):
    project_path: str
    user_goal: str
    goal_mode: str = "autonomous"
    authorization_mode: str = "standard"
    protected_paths: list[str] = []
    external_ai_policy: str = "local_first"
    max_external_ai_calls: int = 0
    user_confirmed_write: bool = False
    interrupt_after_step: int | None = None
    submission_id: str = ""


class RollbackRequest(BaseModel):
    checkpoint_id: str = ""


class TaskResponse(BaseModel):
    id: str
    user_input: str
    goal: str | None = None
    status: str = "pending"


@router.post("/tasks", response_model=TaskResponse)
async def create_task(body: TaskCreate, request: Request):
    """Create a new task (non-streaming, for simple use)."""
    db = request.app.state.db
    task_id = str(uuid.uuid4())[:12]
    await db.execute(
        "INSERT INTO tasks (id, user_input, status) VALUES (?, ?, ?)",
        [task_id, body.user_input, "pending"],
    )
    return TaskResponse(id=task_id, user_input=body.user_input, status="pending")


@router.get("/tasks")
async def list_tasks(request: Request):
    """List recent durable Agent tasks, falling back to legacy database rows."""
    artifacts = artifact_store.list_tasks()
    if artifacts:
        return {"tasks": artifacts}
    db = request.app.state.db
    tasks = await db.fetch_all("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
    return {"tasks": tasks}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    """Get task details with steps and evidence."""
    artifact = artifact_store.get(task_id)
    if artifact:
        return {"task": artifact}
    db = request.app.state.db
    task = await db.fetch_one("SELECT * FROM tasks WHERE id = ?", [task_id])
    if not task:
        return {"error": "Task not found"}
    steps = await db.fetch_all(
        "SELECT * FROM steps WHERE task_id = ? ORDER BY step_index", [task_id]
    )
    evidence = await db.fetch_all(
        "SELECT * FROM evidence WHERE task_id = ? ORDER BY created_at", [task_id]
    )
    return {"task": task, "steps": steps, "evidence": evidence}


@router.get("/tasks/{task_id}/report", response_class=PlainTextResponse)
async def get_task_report(task_id: str):
    """Return the durable final report for a task."""
    report = artifact_store.get_report(task_id)
    if report is None:
        return PlainTextResponse("Task report not found", status_code=404)
    return report


@router.post("/tasks/{task_id}/open")
async def open_task_directory(task_id: str):
    """Open only this app's durable task directory."""
    task = artifact_store.get(task_id)
    if not task:
        return {"error": "Task not found", "task_id": task_id}
    task_dir = artifact_store.task_dir(task_id).resolve()
    root = artifact_store.root.resolve()
    if root not in task_dir.parents:
        return {"error": "Task path rejected", "task_id": task_id}
    try:
        subprocess.Popen(["open", str(task_dir)])
    except OSError as exc:
        return {"error": str(exc), "task_id": task_id}
    return {"task_id": task_id, "opened": True, "task_dir": str(task_dir)}


@router.get("/ai-profiles")
async def list_ai_profiles(request: Request):
    """List available external AI profiles."""
    db = request.app.state.db
    profiles = await db.fetch_all("SELECT * FROM ai_profiles")
    return {"profiles": profiles}


@router.get("/tasks/resumable")
async def list_resumable_tasks():
    """List tasks with persisted StepState checkpoints."""
    from backend.local_model.step_state_store import StepStateStore

    store = StepStateStore()

    def summarize(state):
        return {
            "task_id": state.task_id,
            "current_step_index": state.current_step_index,
            "total_steps": len(state.plan_steps),
            "completed": len(state.completed_steps),
            "failed": len(state.failed_steps),
            "final_goal": state.goal_contract.get("final_goal", ""),
            "authorization_mode": state.authorization_contract.get(
                "authorization_mode", ""
            ),
            "resumable": bool(
                state.goal_contract
                and state.authorization_contract
                and state.plan_steps
            ),
        }

    return {"tasks": [summarize(state) for state in store.list_resumable_tasks()]}


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Return checkpoint data for frontend/WebSocket resume."""
    from backend.local_model.step_state_store import StepStateStore

    state = StepStateStore().load(task_id)
    if not state:
        return {"error": "No checkpoint found", "task_id": task_id}
    return {
        "task_id": task_id,
        "step_state": state.__dict__,
        "resume_payload": {"task_id": task_id, "resume_from_task_id": task_id},
        "websocket": "/ws/execute-contract",
    }


@router.post("/tasks/real-project/run")
async def run_real_project_task(body: RealProjectTaskCreate):
    """Run the bounded real-project completion loop against an explicit copy."""
    from backend.core.real_project_runner import RealProjectRunner

    return RealProjectRunner().run(
        body.project_path,
        body.user_goal,
        goal_mode=body.goal_mode,
        authorization_mode=body.authorization_mode,
        protected_paths=body.protected_paths,
        external_ai_policy=body.external_ai_policy,
        max_external_ai_calls=body.max_external_ai_calls,
        user_confirmed_write=body.user_confirmed_write,
        interrupt_after_step=body.interrupt_after_step,
    )


def _submission_key(body: RealProjectTaskCreate) -> str:
    stable = {
        "project_path": body.project_path,
        "user_goal": body.user_goal,
        "goal_mode": body.goal_mode,
        "authorization_mode": body.authorization_mode,
        "submission_id": body.submission_id,
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()


async def _run_real_project_background(task_id: str, key: str, body: RealProjectTaskCreate):
    from backend.core.real_project_runner import RealProjectRunner

    try:
        await asyncio.to_thread(
            RealProjectRunner().run,
            body.project_path,
            body.user_goal,
            goal_mode=body.goal_mode,
            authorization_mode=body.authorization_mode,
            protected_paths=body.protected_paths,
            external_ai_policy=body.external_ai_policy,
            max_external_ai_calls=body.max_external_ai_calls,
            user_confirmed_write=body.user_confirmed_write,
            task_id=task_id,
            interrupt_after_step=body.interrupt_after_step,
        )
    except Exception as exc:
        artifact_store.update_state(
            task_id,
            status="failed",
            phase="failed",
            failure_reason=str(exc),
        )
        artifact_store.append_event(
            task_id,
            "task_failed",
            stage="failed",
            status="failed",
            summary=f"任务执行失败：{exc}",
            progress_percent=100,
        )
    finally:
        active_real_project_tasks.pop(key, None)


@router.post("/tasks/real-project/async")
async def create_async_real_project_task(body: RealProjectTaskCreate):
    """Create a real-project task immediately and execute it in the background."""
    key = _submission_key(body)
    existing = active_real_project_tasks.get(key)
    if existing:
        return {
            "task_id": existing,
            "status": "already_running",
            "duplicate_prevented": True,
            "events_url": f"/api/tasks/{existing}/events",
        }
    task_id = f"real-{uuid.uuid4().hex[:10]}"
    active_real_project_tasks[key] = task_id
    artifact_store.update_state(
        task_id,
        status="created",
        phase="queued",
        project_path=body.project_path,
        user_input=body.user_goal,
        submission_key=key,
    )
    artifact_store.append_event(
        task_id,
        "task_created",
        stage="queued",
        status="created",
        summary="任务已创建，正在进入后台执行",
        progress_percent=0,
    )
    asyncio.create_task(_run_real_project_background(task_id, key, body))
    return {
        "task_id": task_id,
        "status": "created",
        "duplicate_prevented": False,
        "events_url": f"/api/tasks/{task_id}/events",
    }


@router.get("/tasks/{task_id}/events/history")
async def task_event_history(task_id: str, after: int = 0):
    return {"task_id": task_id, "events": artifact_store.list_events(task_id, after)}


@router.get("/tasks/{task_id}/events")
async def stream_task_events(task_id: str, request: Request, after: int = 0):
    """Replay persisted events and continue with an SSE stream."""
    header_cursor = request.headers.get("last-event-id", "")
    cursor = int(header_cursor) if header_cursor.isdigit() else max(0, int(after or 0))

    async def generate():
        nonlocal cursor
        idle_ticks = 0
        terminal = {"task_completed", "task_failed", "task_paused"}
        while True:
            if await request.is_disconnected():
                return
            events = artifact_store.list_events(task_id, cursor)
            if events:
                idle_ticks = 0
                for event in events:
                    cursor = int(event["event_id"])
                    yield (
                        f"id: {cursor}\n"
                        "event: task_event\n"
                        f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    )
                    if event["event_type"] in terminal:
                        return
            else:
                idle_ticks += 1
                if idle_ticks % 20 == 0:
                    yield ": heartbeat\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/tasks/real-project/prepare")
async def prepare_real_project_task(body: RealProjectTaskCreate):
    """Preview the Goal Contract and plan without modifying the project."""
    from backend.core.real_project_runner import RealProjectRunner

    return RealProjectRunner().prepare(
        body.project_path,
        body.user_goal,
        goal_mode=body.goal_mode,
        authorization_mode=body.authorization_mode,
        protected_paths=body.protected_paths,
        external_ai_policy=body.external_ai_policy,
        max_external_ai_calls=body.max_external_ai_calls,
    )


@router.post("/tasks/{task_id}/resume-real-project")
async def resume_real_project_task(task_id: str):
    from backend.core.real_project_runner import RealProjectRunner

    return RealProjectRunner().resume(task_id)


async def _resume_real_project_background(task_id: str):
    from backend.core.real_project_runner import RealProjectRunner

    key = f"resume:{task_id}"
    try:
        await asyncio.to_thread(RealProjectRunner().resume, task_id)
    except Exception as exc:
        artifact_store.update_state(task_id, status="failed", failure_reason=str(exc))
        artifact_store.append_event(
            task_id,
            "task_failed",
            stage="resume",
            status="failed",
            summary=f"任务恢复失败：{exc}",
            progress_percent=100,
        )
    finally:
        active_real_project_tasks.pop(key, None)


@router.post("/tasks/{task_id}/resume-real-project-async")
async def resume_real_project_task_async(task_id: str):
    key = f"resume:{task_id}"
    if key in active_real_project_tasks:
        return {
            "task_id": task_id,
            "status": "already_running",
            "duplicate_prevented": True,
            "events_url": f"/api/tasks/{task_id}/events",
        }
    state = artifact_store.get(task_id)
    if not state:
        return {"task_id": task_id, "status": "failed", "failure_reason": "task_not_found"}
    active_real_project_tasks[key] = task_id
    asyncio.create_task(_resume_real_project_background(task_id))
    return {
        "task_id": task_id,
        "status": "resuming",
        "duplicate_prevented": False,
        "events_url": f"/api/tasks/{task_id}/events",
        "after_event_id": state.get("event_count", 0),
    }


@router.get("/tasks/{task_id}/checkpoints")
async def list_task_checkpoints(task_id: str):
    from backend.core.real_project_runner import RealProjectRunner

    return {
        "task_id": task_id,
        "checkpoints": RealProjectRunner().list_checkpoints(task_id),
    }


@router.post("/tasks/{task_id}/rollback")
async def rollback_task(task_id: str, body: RollbackRequest):
    from backend.core.real_project_runner import RealProjectRunner

    return RealProjectRunner().rollback(task_id, body.checkpoint_id)
