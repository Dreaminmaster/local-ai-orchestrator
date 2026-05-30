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
                await websocket.send_json(
                    {"type": "error", "data": {"message": "Empty input"}}
                )
                continue

            # Create agent and run
            agent = Agent()

            try:
                async for event in agent.run(user_input):
                    await websocket.send_text(event.to_json())
            except Exception as e:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {
                            "message": str(e),
                            "traceback": traceback.format_exc(),
                        },
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        except Exception:
            pass


@router.websocket("/execute-contract")
async def execute_contract_task(websocket: WebSocket):
    """
    Contract-based streaming execution.

    Client sends:
    {
      "goal_contract": {...},
      "authorization_contract": {...}
    }
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            task_id = data.get("task_id")
            goal_contract = data.get("goal_contract")
            authorization_contract = data.get("authorization_contract")
            if task_id and not (goal_contract and authorization_contract):
                agent = Agent()
                async for event in agent.resume_from_step_state(task_id):
                    await websocket.send_text(event.to_json())
                continue
            if not goal_contract or not authorization_contract:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {
                            "message": "goal_contract and authorization_contract required"
                        },
                    }
                )
                continue
            agent = Agent()
            try:
                async for event in agent.run_with_contracts(
                    goal_contract, authorization_contract
                ):
                    await websocket.send_text(event.to_json())
            except Exception as e:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {
                            "message": str(e),
                            "traceback": traceback.format_exc(),
                        },
                    }
                )
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        except Exception:
            pass
