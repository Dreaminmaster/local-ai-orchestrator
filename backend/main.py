"""
Local AI Self-Supervised Orchestrator — FastAPI Backend Entry Point
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.storage.database import Database
from backend.api.tasks import router as tasks_router
from backend.api.skills import router as skills_router
from backend.api.websocket import router as ws_router
from backend.api.confirmations import router as confirmations_router
from backend.api.contracts import router as contracts_router

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    await db.initialize()
    app.state.db = db
    yield
    await db.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Local AI Orchestrator",
    description="本地 AI 自监督总控系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(tasks_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(confirmations_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")

# Serve frontend
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def main():
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8422"))
    print(f"\n🧠 Local AI Orchestrator starting on http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
