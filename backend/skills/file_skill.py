"""File Skill — Read, write, modify files with snapshot support."""

from __future__ import annotations
import shutil
import json
from datetime import datetime
from pathlib import Path
from .base import Skill, SkillResult, RiskLevel


class FileSkill(Skill):
    name = "file"
    description = "Read, write, and modify files with automatic snapshots"
    capabilities = [
        "read_file",
        "write_file",
        "modify_file",
        "list_directory",
        "create_directory",
        "delete_file",
        "copy_file",
        "snapshot",
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
            elif action == "targeted_replace":
                return await self._modify_file(
                    path,
                    context.get("old_string", ""),
                    context.get("new_string", ""),
                )
            elif action == "apply_patch":
                return await self._apply_patch(
                    path,
                    context.get("patch", ""),
                    dry_run=bool(context.get("dry_run", False)),
                )
            elif action == "backup_before_write":
                return await self._take_snapshot(path)
            elif action == "restore_backup":
                return await self._restore_backup(path, context.get("backup_path", ""))
            else:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=str(e),
            )

    async def _read_file(self, path: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"File not found: {path}",
            )
        content = p.read_text(encoding="utf-8", errors="replace")
        return SkillResult(
            skill=self.name,
            success=True,
            result=content[:10000],
            metadata={
                "path": path,
                "size": p.stat().st_size,
                "lines": content.count("\n") + 1,
            },
        )

    async def _write_file(self, path: str, content: str) -> SkillResult:
        p = Path(path)
        # Take snapshot before overwriting
        if p.exists():
            await self._take_snapshot(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Written {len(content)} bytes to {path}",
            evidence=[path],
        )

    async def _modify_file(self, path: str, old_str: str, new_str: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"File not found: {path}",
            )
        await self._take_snapshot(path)
        content = p.read_text(encoding="utf-8")
        if old_str not in content:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"String not found in file: {old_str[:100]}...",
            )
        new_content = content.replace(old_str, new_str, 1)
        p.write_text(new_content, encoding="utf-8")
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Modified {path}: replaced text",
            evidence=[path],
        )

    async def _list_directory(self, path: str) -> SkillResult:
        p = Path(path or ".")
        if not p.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Directory not found: {path}",
            )
        entries = []
        for item in sorted(p.iterdir()):
            kind = "dir" if item.is_dir() else "file"
            size = item.stat().st_size if item.is_file() else 0
            entries.append({"name": item.name, "type": kind, "size": size})
        return SkillResult(
            skill=self.name,
            success=True,
            result=json.dumps(entries, ensure_ascii=False, indent=2),
            metadata={"path": str(p), "count": len(entries)},
        )

    async def _create_directory(self, path: str) -> SkillResult:
        Path(path).mkdir(parents=True, exist_ok=True)
        return SkillResult(
            skill=self.name, success=True, result=f"Directory created: {path}"
        )

    async def _delete_file(self, path: str) -> SkillResult:
        self.risk_level = RiskLevel.HIGH
        p = Path(path)
        if not p.exists():
            return SkillResult(
                skill=self.name, success=False, result="", error=f"Not found: {path}"
            )
        await self._take_snapshot(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Deleted: {path}",
            evidence=[path],
        )

    async def _apply_patch(
        self,
        path: str,
        patch: str,
        dry_run: bool = False,
    ) -> SkillResult:
        """Apply a small safe patch.

        Supported patch formats:
        - prepend:<text>
        - append:<text>
        - targeted_replace:<old>|||<new>
        - line_replace:<line_number>|||<new_line>
        - insert_before:<marker>|||<text>
        - insert_after:<marker>|||<text>
        - unified_diff:<diff> (reserved; returns unsupported for now)
        """
        target = Path(path)
        if not target.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"File not found: {path}",
            )
        original = target.read_text(encoding="utf-8")
        new_content = original
        operation = "unknown"
        if patch.startswith("prepend:"):
            operation = "prepend"
            new_content = patch[len("prepend:") :] + original
        elif patch.startswith("append:"):
            operation = "append"
            new_content = original + patch[len("append:") :]
        elif patch.startswith("targeted_replace:"):
            operation = "targeted_replace"
            payload = patch[len("targeted_replace:") :]
            old, sep, new = payload.partition("|||")
            if not sep or old not in original:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error="targeted_replace requires old|||new and old must exist",
                )
            new_content = original.replace(old, new, 1)
        elif patch.startswith("line_replace:"):
            operation = "line_replace"
            payload = patch[len("line_replace:") :]
            line_no_raw, sep, new_line = payload.partition("|||")
            if not sep:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error="line_replace requires line_number|||new_line",
                )
            line_no = int(line_no_raw)
            lines = original.splitlines(keepends=True)
            if line_no < 1 or line_no > len(lines):
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error=f"line out of range: {line_no}",
                )
            newline = "\n" if lines[line_no - 1].endswith("\n") else ""
            lines[line_no - 1] = new_line + newline
            new_content = "".join(lines)
        elif patch.startswith("insert_before:"):
            operation = "insert_before"
            payload = patch[len("insert_before:") :]
            marker, sep, insert_text = payload.partition("|||")
            if not sep or marker not in original:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error="insert_before requires marker|||text and marker must exist",
                )
            new_content = original.replace(marker, insert_text + marker, 1)
        elif patch.startswith("insert_after:"):
            operation = "insert_after"
            payload = patch[len("insert_after:") :]
            marker, sep, insert_text = payload.partition("|||")
            if not sep or marker not in original:
                return SkillResult(
                    skill=self.name,
                    success=False,
                    result="",
                    error="insert_after requires marker|||text and marker must exist",
                )
            new_content = original.replace(marker, marker + insert_text, 1)
        elif patch.startswith("unified_diff:"):
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error="unified_diff patching is reserved but not enabled yet",
            )
        else:
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error="Unsupported patch format",
            )
        if dry_run:
            return SkillResult(
                skill=self.name,
                success=True,
                result=f"Dry run patch {operation} would change {path}",
                metadata={"operation": operation, "changed": new_content != original},
            )
        snapshot = await self._take_snapshot(path)
        backup_path = (
            snapshot.evidence[0] if snapshot.success and snapshot.evidence else None
        )
        try:
            target.write_text(new_content, encoding="utf-8")
        except Exception as exc:
            if backup_path:
                await self._restore_backup(path, backup_path)
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Patch failed and backup restored: {exc}",
                evidence=[backup_path] if backup_path else [],
            )
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Patch applied to {path} ({operation})",
            evidence=[path] + ([backup_path] if backup_path else []),
            metadata={"operation": operation, "backup_path": backup_path},
        )

    async def _restore_backup(self, path: str, backup_path: str) -> SkillResult:
        if not backup_path:
            return SkillResult(
                skill=self.name, success=False, result="", error="backup_path required"
            )
        src = Path(backup_path)
        dst = Path(path)
        if not src.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error=f"Backup not found: {backup_path}",
            )
        shutil.copy2(src, dst)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Restored {path} from {backup_path}",
            evidence=[path],
        )

    async def _take_snapshot(self, path: str) -> SkillResult:
        p = Path(path)
        if not p.exists():
            return SkillResult(
                skill=self.name,
                success=False,
                result="",
                error="File not found for snapshot",
            )
        snap_dir = p.parent / self.SNAPSHOT_DIR
        snap_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = snap_dir / f"{p.name}.{ts}.bak"
        shutil.copy2(p, snap_path)
        return SkillResult(
            skill=self.name,
            success=True,
            result=f"Snapshot saved: {snap_path}",
            evidence=[str(snap_path)],
        )
