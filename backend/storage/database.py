"""SQLite database layer with async support."""
import aiosqlite
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parent / "orchestrator.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    user_input TEXT NOT NULL,
    goal TEXT,
    task_type TEXT,
    status TEXT DEFAULT 'pending',
    success_criteria TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    skill_used TEXT,
    result TEXT,
    error TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT,
    type TEXT NOT NULL,
    source TEXT,
    file_path TEXT,
    content TEXT,
    supports TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS ai_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mode TEXT DEFAULT 'api',
    status TEXT DEFAULT 'unknown',
    strengths TEXT,
    weaknesses TEXT,
    best_for TEXT
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS task_memory (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""


class Database:
    def __init__(self, path: str | None = None):
        self.path = path or DB_PATH
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        await self._seed_ai_profiles()

    async def close(self):
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn, "Database not initialized"
        return self._conn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def execute(self, sql: str, params=None):
        cursor = await self.conn.execute(sql, params or [])
        await self.conn.commit()
        return cursor

    async def fetch_one(self, sql: str, params=None) -> dict | None:
        cursor = await self.conn.execute(sql, params or [])
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params=None) -> list[dict]:
        cursor = await self.conn.execute(sql, params or [])
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    async def _seed_ai_profiles(self):
        profiles = [
            ("chatgpt", "ChatGPT", "api", "available",
             '["综合方案","图像理解","写作","通用推理"]',
             '["可能产生幻觉","长文可能截断"]',
             '["通用问答","创意写作","图像分析"]'),
            ("claude", "Claude", "api", "available",
             '["长文分析","复杂逻辑","代码解释","方案评审"]',
             '["视觉能力取决于版本"]',
             '["复杂方案","技术架构","长文总结"]'),
            ("deepseek", "DeepSeek", "api", "available",
             '["代码能力强","推理能力强","中文优秀"]',
             '["多模态能力有限"]',
             '["代码生成","数学推理","中文任务"]'),
            ("gemini", "Gemini", "api", "unknown",
             '["视觉理解","跨模态分析","长上下文"]',
             '["中文能力一般"]',
             '["视觉分析","多模态任务"]'),
        ]
        for p in profiles:
            await self.conn.execute(
                "INSERT OR IGNORE INTO ai_profiles (id,name,mode,status,strengths,weaknesses,best_for) VALUES (?,?,?,?,?,?,?)",
                p,
            )
        await self.conn.commit()
