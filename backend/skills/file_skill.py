"""File Skill — Read, write, modify files with snapshot support."""
from __future__ import annotations
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from .base import Skill, SkillResult, RiskLevel


class FileSkill(Skill):
    name = "file"
    description = "Read, write, and modify files with automatic snapshots"
    capabilities = [
        "read_file", "write_file", "modify_file", "list_directory",
        "create_directory", "delete_file", "copy_file", "snapshot",
    ]
    risk_level = RiskLevel.MEDIUM

    SNAPSHOT_DIR = ".snapshots"

    async def can_handle(self, task: dict, state: dict) -> bool:
        keywords = ["file", "read", "write", "modify", "create", "delete", "directory"]
        desc = task.get("description", "").lower()
        return any(k in desc for k in keywords)

    async def execute(self, instruction: str, context: dict) -> SkillResult:
        action = context.get("action", "read_file")
        path = context.get("path", "")

        try:
            if action == "read_file":
                return await self._read_file(path)
            elif action == "write_file":
                content = context.get("content", "")
                return await self._write_file(path, content)
            elif action == "modify_file":
                old_str = context.get("old_string", "")
                new_str = context.get("new_string", "")
                return await self._modify_file(path, old_str, new_str)
            elif action == "list_directory":
                return await self._list_directory(path)
            elif action == "create_directory":
                return await self._create_directory(path)
            elif action == "delete_file":
                return await self._delete_file(path)
            elif action == "snapshot":
                return await self._take_snapshot(path)
            else:
                return SkillResult(
                    skill=self.name, success=False, result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(
                skill=self.name, success=False, result="", error=str(e),
            )

    async def _read_file(self, path: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(skill=self.name, success=False, result="", error=f"File not found: {path}")
        content = p.read_text(encoding="utf-8", errors="replace")
        return SkillResult(
            skill=self.name, success=True, result=content[:10000],
            metadata={"path": path, "size": p.stat().st_size, "lines": content.count("\n") + 1},
        )

    async def _write_file(self, path: str, content: str) -> SkillResult:
        p = Path(path)
        # Take snapshot before overwriting
        if p.exists():
            await self._take_snapshot(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return SkillResult(
            skill=self.name, success=True,
            result=f"Written {len(content)} bytes to {path}",
            evidence=[path],
        )

    async def _modify_file(self, path: str, old_str: str, new_str: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(skill=self.name, success=False, result="", error=f"File not found: {path}")
        await self._take_snapshot(path)
        content = p.read_text(encoding="utf-8")
        if old_str not in content:
            return SkillResult(
                skill=self.name, success=False, result="",
                error=f"String not found in file: {old_str[:100]}...",
            )
        new_content = content.replace(old_str, new_str, 1)
        p.write_text(new_content, encoding="utf-8")
        return SkillResult(
            skill=self.name, success=True,
            result=f"Modified {path}: replaced text",
            evidence=[path],
        )

    async def _list_directory(self, path: str) -> SkillResult:
        p = Path(path or ".")
        if not p.exists():
            return SkillResult(skill=self.name, success=False, result="", error=f"Directory not found: {path}")
        entries = []
        for item in sorted(p.iterdir()):
            kind = "dir" if item.is_dir() else "file"
            size = item.stat().st_size if item.is_file() else 0
            entries.append({"name": item.name, "type": kind, "size": size})
        return SkillResult(
            skill=self.name, success=True,
            result=json.dumps(entries, ensure_ascii=False, indent=2),
            metadata={"path": str(p), "count": len(entries)},
        )

    async def _create_directory(self, path: str) -> SkillResult:
        Path(path).mkdir(parents=True, exist_ok=True)
        return SkillResult(skill=self.name, success=True, result=f"Directory created: {path}")

    async def _delete_file(self, path: str) -> SkillResult:
        self.risk_level = RiskLevel.HIGH
        p = Path(path)
        if not p.exists():
            return SkillResult(skill=self.name, success=False, result="", error=f"Not found: {path}")
        await self._take_snapshot(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        return SkillResult(
            skill=self.name, success=True, result=f"Deleted: {path}", evidence=[path],
        )

    async def _take_snapshot(self, path: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(skill=self.name, success=False, result="", error="File not found for snapshot")
        snap_dir = p.parent / self.SNAPSHOT_DIR
        snap_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = snap_dir / f"{p.name}.{ts}.bak"
        shutil.copy2(p, snap_path)
        return SkillResult(
            skill=self.name, success=True,
            result=f"Snapshot saved: {snap_path}",
            evidence=[str(snap_path)],
        )
