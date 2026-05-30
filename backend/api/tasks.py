"""Tasks API — Create and manage tasks."""

from __future__ import annotations
import uuid
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["tasks"])


class TaskCreate(BaseModel):
    user_input: str


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
    """List all tasks."""
    db = request.app.state.db
    tasks = await db.fetch_all("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
    return {"tasks": tasks}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    """Get task details with steps and evidence."""
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
    return {"tasks": [state.__dict__ for state in store.list_resumable_tasks()]}


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Return checkpoint data for frontend/WebSocket resume."""
    from backend.local_model.step_state_store import StepStateStore

    state = StepStateStore().load(task_id)
    if not state:
        return {"error": "No checkpoint found", "task_id": task_id}
    return {"task_id": task_id, "step_state": state.__dict__}
