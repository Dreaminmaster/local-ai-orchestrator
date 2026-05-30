"""WebSocket API — Real-time task execution with streaming events."""
from __future__ import annotations
import json
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.core.agent import Agent

router = APIRouter()


@router.websocket("/execute")
async def execute_task(websocket: WebSocket):
    """
    WebSocket endpoint for real-time task execution.

    Client sends: {"user_input": "帮我把这个网页做得更高级"}
    Server streams: {"type": "phase", "data": {...}, "timestamp": "..."}
    """
    await websocket.accept()

    try:
        while True:
            # Wait for task input
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_input = data.get("user_input", "")

            if not user_input:
                await websocket.send_json({"type": "error", "data": {"message": "Empty input"}})
                continue

            # Create agent and run
            agent = Agent()

            try:
                async for event in agent.run(user_input):
                    await websocket.send_text(event.to_json())
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    },
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        except Exception:
            pass
