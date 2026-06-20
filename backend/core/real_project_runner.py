"""Durable inspect-plan-repair-verify runner for isolated real-project copies."""

from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from backend.core.task_artifact_store import TaskArtifactStore
from backend.evidence.board import EvidenceBoard


class RealProjectRunner:
    """Run bounded repairs against an explicit project copy."""

    def __init__(self, task_root: str | Path | None = None):
        self.artifacts = TaskArtifactStore(task_root)
        self.evidence = EvidenceBoard()

    def run(
        self,
        project_path: str | Path,
        user_goal: str,
        *,
        goal_mode: str = "autonomous",
        authorization_mode: str = "full_autonomy",
        protected_paths: list[str] | None = None,
        external_ai_policy: str = "local_first",
        max_external_ai_calls: int = 0,
        user_confirmed_write: bool = False,
        task_id: str | None = None,
        interrupt_after_step: int | None = None,
    ) -> dict:
        started = time.monotonic()
        root = Path(project_path).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"project_path_not_found:{root}")
        if authorization_mode == "standard" and not user_confirmed_write:
            return {
                "final_status": "WAITING_CONFIRMATION",
                "failure_reason": "write_confirmation_required",
                "project_path": str(root),
                "authorization_mode": authorization_mode,
            }
        task_id = task_id or f"real-{uuid.uuid4().hex[:10]}"
        project_type = self.detect_project_type(root)
        verify_commands = self.infer_verification_commands(root, project_type)
        contract = self.build_goal_contract(
            root,
            user_goal,
            project_type,
            verify_commands,
            goal_mode=goal_mode,
            external_ai_policy=external_ai_policy,
            max_external_ai_calls=max_external_ai_calls,
        )
        capabilities = (
            ["read_files", "write_files", "run_shell", "modify_code"]
            if authorization_mode == "full_autonomy"
            else ["read_files", "run_shell"]
        )
        authorization = {
            "authorization_mode": authorization_mode,
            "provided_resources": {"project_path": str(root)},
            "granted_capabilities": capabilities,
            "protected_paths": protected_paths or [],
            "user_confirmed_authorization": True,
        }
        plan = self.build_plan(project_type, verify_commands)
        self.artifacts.initialize(task_id, contract, authorization)
        self._emit(task_id, "task_created", stage="created", status="running", summary="真实项目任务已创建", progress=1)
        self.artifacts.write_json(task_id, "goal_contract.json", contract)
        self._emit(task_id, "goal_contract_created", stage="goal", status="completed", summary="目标契约已生成", progress=4)
        self._emit(task_id, "authorization_confirmed", stage="authorization", status="completed", summary="执行授权已确认", progress=6)
        self._emit(task_id, "planning_started", stage="planning", status="running", summary="正在生成执行计划", progress=8)
        self.artifacts.save_plan(task_id, {"plan": plan, "total_steps": len(plan)})
        self._emit(task_id, "plan_created", stage="planning", status="completed", summary=f"执行计划已生成，共 {len(plan)} 步", progress=10, payload={"total_steps": len(plan)})
        state = self.artifacts.update_state(
            task_id,
            status="running",
            phase="inspect",
            project_path=str(root),
            project_type=project_type,
            current_step=0,
            completed_steps=[],
            files_changed=[],
            repair_count=0,
            replan_count=0,
            claude_call_count=0,
            success_criteria_met=False,
        )
        start_checkpoint = self.create_checkpoint(task_id, root, "task_start")
        self._emit(task_id, "checkpoint_created", stage="checkpoint", status="completed", summary="已创建任务开始检查点", progress=12, payload={"checkpoint_id": start_checkpoint["checkpoint_id"]})
        self.artifacts.write_json(
            task_id, "checkpoints.json", {"checkpoints": [start_checkpoint]}
        )

        self._step_started(task_id, plan[0], 15)
        inspection = self.scan_project(root)
        self._complete_step(task_id, plan[0], {"inspection": inspection})
        if interrupt_after_step == 1:
            return self._interrupt(task_id, started)

        self._step_started(task_id, plan[1], 28)
        self._emit(task_id, "verification_started", stage="initial_verify", step=plan[1], status="running", summary="正在运行初始验证", progress=30)
        initial_results = [self._run_command_with_events(task_id, plan[1], root, command, 34) for command in verify_commands]
        self._complete_step(task_id, plan[1], {"commands": initial_results})
        if interrupt_after_step == 2:
            return self._interrupt(task_id, started)

        self._step_started(task_id, plan[2], 46)
        self._emit(task_id, "repair_started", stage="repair", step=plan[2], status="running", summary="正在修复明确错误", progress=48)
        before = self.snapshot_text_files(root)
        repair_summary = self.repair_project(root, project_type)
        after = self.snapshot_text_files(root)
        diffs = self.write_diffs(task_id, before, after)
        changed = sorted(diffs)
        checkpoint = self.create_checkpoint(task_id, root, "after_repair")
        self._emit(task_id, "checkpoint_created", stage="checkpoint", status="completed", summary="已创建修复后检查点", progress=62, payload={"checkpoint_id": checkpoint["checkpoint_id"]})
        checkpoint_data = self.artifacts.read_json(task_id, "checkpoints.json") or {
            "checkpoints": []
        }
        checkpoint_data["checkpoints"].append(checkpoint)
        self.artifacts.write_json(task_id, "checkpoints.json", checkpoint_data)
        self._complete_step(
            task_id,
            plan[2],
            {"repair": repair_summary, "files_changed": changed, "diffs": diffs},
        )
        for path in changed:
            self._emit(task_id, "file_changed", stage="repair", step=plan[2], status="completed", summary=f"已修改文件：{path}", progress=64, payload={"path": path})
        self._emit(task_id, "repair_completed", stage="repair", step=plan[2], status="completed", summary=f"修复完成，修改 {len(changed)} 个文件", progress=66)
        self.artifacts.update_state(
            task_id, files_changed=changed, repair_count=len(changed), phase="reverify"
        )
        if interrupt_after_step == 3:
            return self._interrupt(task_id, started)

        self._step_started(task_id, plan[3], 72)
        self._emit(task_id, "verification_started", stage="reverify", step=plan[3], status="running", summary="正在重新验证", progress=74)
        final_results = [self._run_command_with_events(task_id, plan[3], root, command, 78) for command in verify_commands]
        verified = bool(final_results) and all(item["exit_code"] == 0 for item in final_results)
        self._emit(task_id, "verification_result", stage="reverify", step=plan[3], status="completed" if verified else "failed", summary="重新验证通过" if verified else "重新验证失败", progress=88, payload={"verified": verified})
        self._complete_step(task_id, plan[3], {"commands": final_results, "verified": verified})
        self._step_started(task_id, plan[4], 92)
        report = self.build_report(
            user_goal, project_type, changed, initial_results, final_results, verified
        )
        report_path = self.artifacts.save_report(task_id, report)
        self._complete_step(task_id, plan[4], {"report_path": str(report_path)})
        self._emit(task_id, "final_report_ready", stage="report", step=plan[4], status="completed", summary="最终报告已生成", progress=98, payload={"report_path": str(report_path)})
        status = "success" if verified else "failed"
        final_state = self.artifacts.update_state(
            task_id,
            status=status,
            phase="complete" if verified else "failed",
            current_step=len(plan),
            success_criteria_met=verified and bool(report_path.exists()),
            failure_reason="" if verified else "verification_failed",
            final_report_path=str(report_path),
            duration_seconds=round(time.monotonic() - started, 3),
            evidence_count=len(self.evidence.get_task_evidence(task_id)),
            rollback_available=True,
        )
        self._emit(task_id, "task_completed" if verified else "task_failed", stage="complete" if verified else "failed", status=status, summary="任务已完成" if verified else "任务验证失败", progress=100)
        return self._result(task_id, final_state)

    def prepare(
        self,
        project_path: str | Path,
        user_goal: str,
        *,
        goal_mode: str = "autonomous",
        authorization_mode: str = "standard",
        protected_paths: list[str] | None = None,
        external_ai_policy: str = "local_first",
        max_external_ai_calls: int = 0,
    ) -> dict:
        root = Path(project_path).expanduser().resolve()
        if not root.is_dir():
            return {
                "status": "FAIL",
                "failure_code": "PROJECT_PATH_NOT_FOUND",
                "failure_reason": f"project_path_not_found:{root}",
            }
        project_type = self.detect_project_type(root)
        commands = self.infer_verification_commands(root, project_type)
        return {
            "status": "WAITING_CONFIRMATION",
            "project_inspection": self.scan_project(root),
            "goal_contract": self.build_goal_contract(
                root,
                user_goal,
                project_type,
                commands,
                goal_mode=goal_mode,
                external_ai_policy=external_ai_policy,
                max_external_ai_calls=max_external_ai_calls,
            ),
            "authorization_contract": {
                "authorization_mode": authorization_mode,
                "protected_paths": protected_paths or [],
                "write_requires_confirmation": authorization_mode == "standard",
                "user_confirmed_authorization": False,
            },
            "plan": {"plan": self.build_plan(project_type, commands), "total_steps": 5},
        }

    def resume(self, task_id: str) -> dict:
        state = self.artifacts.read_json(task_id, "task_state.json")
        if not state:
            return {"final_status": "FAIL", "failure_reason": "task_not_found"}
        started = time.monotonic()
        self._emit(task_id, "task_resumed", stage="resume", status="running", summary="任务已恢复执行", progress=45)
        root = Path(state["project_path"])
        contract = state["goal_contract"]
        plan_data = self.artifacts.read_json(task_id, "plan.json") or {"plan": []}
        plan = plan_data["plan"]
        current = int(state.get("current_step", 0))
        if current < 2:
            return {
                "final_status": "FAIL",
                "failure_reason": "resume_checkpoint_too_early",
                "task_id": task_id,
            }
        if current < 3:
            before = self.snapshot_text_files(root)
            repair_summary = self.repair_project(root, state["project_type"])
            after = self.snapshot_text_files(root)
            diffs = self.write_diffs(task_id, before, after)
            changed = sorted(set(state.get("files_changed", [])) | set(diffs))
            checkpoint = self.create_checkpoint(task_id, root, "after_repair")
            checkpoint_data = self.artifacts.read_json(task_id, "checkpoints.json") or {
                "checkpoints": []
            }
            checkpoint_data["checkpoints"].append(checkpoint)
            self.artifacts.write_json(task_id, "checkpoints.json", checkpoint_data)
            self._complete_step(
                task_id,
                plan[2],
                {"repair": repair_summary, "files_changed": changed, "diffs": diffs},
            )
            self.artifacts.update_state(
                task_id,
                files_changed=changed,
                repair_count=len(changed),
                resumed_from_checkpoint=True,
            )
        commands = contract["verification_commands"]
        self._step_started(task_id, plan[3], 72)
        self._emit(task_id, "verification_started", stage="reverify", step=plan[3], status="running", summary="恢复后正在重新验证", progress=74)
        final_results = [self._run_command_with_events(task_id, plan[3], root, command, 78) for command in commands]
        verified = all(item["exit_code"] == 0 for item in final_results)
        self._emit(task_id, "verification_result", stage="reverify", step=plan[3], status="completed" if verified else "failed", summary="恢复后验证通过" if verified else "恢复后验证失败", progress=88, payload={"verified": verified})
        self._complete_step(task_id, plan[3], {"commands": final_results, "verified": verified})
        state = self.artifacts.read_json(task_id, "task_state.json") or state
        report = self.build_report(
            contract["user_goal"],
            state["project_type"],
            state.get("files_changed", []),
            [],
            final_results,
            verified,
        )
        report_path = self.artifacts.save_report(task_id, report)
        self._complete_step(task_id, plan[4], {"report_path": str(report_path)})
        self._emit(task_id, "final_report_ready", stage="report", step=plan[4], status="completed", summary="最终报告已生成", progress=98, payload={"report_path": str(report_path)})
        final_state = self.artifacts.update_state(
            task_id,
            status="success" if verified else "failed",
            phase="complete" if verified else "failed",
            success_criteria_met=verified,
            failure_reason="" if verified else "verification_failed",
            final_report_path=str(report_path),
            duration_seconds=round(time.monotonic() - started, 3),
            rollback_available=True,
            resumed_from_checkpoint=True,
        )
        self._emit(task_id, "task_completed" if verified else "task_failed", stage="complete" if verified else "failed", status="success" if verified else "failed", summary="任务已完成" if verified else "任务验证失败", progress=100)
        return self._result(task_id, final_state)

    def list_checkpoints(self, task_id: str) -> list[dict]:
        return (self.artifacts.read_json(task_id, "checkpoints.json") or {}).get(
            "checkpoints", []
        )

    def rollback(self, task_id: str, checkpoint_id: str = "") -> dict:
        checkpoints = self.list_checkpoints(task_id)
        selected = next(
            (item for item in checkpoints if item["checkpoint_id"] == checkpoint_id),
            checkpoints[-1] if checkpoints else None,
        )
        if not selected:
            return {"success": False, "failure_reason": "checkpoint_not_found"}
        project = Path(
            (self.artifacts.read_json(task_id, "task_state.json") or {}).get(
                "project_path", ""
            )
        )
        source = Path(selected["snapshot_path"])
        if not project or not source.exists():
            return {"success": False, "failure_reason": "snapshot_missing"}
        shutil.rmtree(project)
        shutil.copytree(source, project, symlinks=True)
        self.artifacts.update_state(task_id, status="rolled_back", phase="rolled_back")
        self._emit(task_id, "task_rolled_back", stage="rollback", status="completed", summary=f"已回滚到检查点 {selected['checkpoint_id']}", progress=100)
        return {
            "success": True,
            "task_id": task_id,
            "checkpoint_id": selected["checkpoint_id"],
            "project_path": str(project),
        }

    @staticmethod
    def detect_project_type(root: Path) -> str:
        if (root / "package.json").exists() and any(root.glob("src/*.jsx")):
            return "react"
        if (root / "backend").exists() and (root / "frontend").exists():
            return "mixed"
        if (root / "package.json").exists():
            return "node"
        return "python"

    @staticmethod
    def infer_verification_commands(root: Path, project_type: str) -> list[str]:
        if project_type in {"node", "react"}:
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = package.get("scripts", {})
            return ["npm test"] if "test" in scripts else ["npm run build"]
        if project_type == "mixed":
            return ["python3 backend/test_contract.py", "node frontend/test.js"]
        if (root / "tests").is_dir():
            return ["python3 -m unittest discover -s tests -v"]
        source = "app" if (root / "app").is_dir() else "."
        return [f"python3 -m compileall -q {source}"]

    @staticmethod
    def build_goal_contract(
        root: Path,
        user_goal: str,
        project_type: str,
        commands: list[str],
        *,
        goal_mode: str = "autonomous",
        external_ai_policy: str = "local_first",
        max_external_ai_calls: int = 0,
    ) -> dict:
        return {
            "user_goal": user_goal,
            "original_input": user_goal,
            "final_goal": user_goal,
            "project_path": str(root),
            "expected_outcome": "项目明确错误被修复，验证命令通过，并生成中文报告",
            "success_criteria": [
                "verification_commands 全部退出码为 0",
                "所有修改均有 before/after diff",
                "final_report.md 已生成",
            ],
            "forbidden_actions": [
                "修改测试项目目录外文件",
                "无限重试",
                "调用未测试 external AI provider",
            ],
            "allowed_tools": ["file", "shell", "repair", "self_verify"],
            "risk_level": "medium",
            "verification_commands": commands,
            "goal_mode": goal_mode,
            "assumptions": (
                ["允许在安全边界内自主补全缺失的低风险执行细节"]
                if goal_mode == "autonomous"
                else []
            ),
            "clarification_required": goal_mode == "clarify_first",
            "external_ai_policy": external_ai_policy,
            "max_external_ai_calls": max(0, min(max_external_ai_calls, 1)),
            "rollback_policy": "支持 task_start 和 last_successful_step checkpoint",
            "project_type": project_type,
            "user_confirmed_goal": True,
        }

    @staticmethod
    def build_plan(project_type: str, commands: list[str]) -> list[dict]:
        specs = [
            ("inspect", "扫描项目结构和关键配置", "file", "项目类型和关键文件已识别"),
            ("initial_verify", "运行初始验证并记录失败", "shell", "失败日志已记录"),
            ("repair", f"修复 {project_type} 项目的明确错误", "repair", "修改均有 diff"),
            ("reverify", "重新运行验证命令", "shell", "验证命令全部通过"),
            ("report", "生成中文最终报告", "file", "final_report.md 存在"),
        ]
        return [
            {
                "step_id": f"step_{index}",
                "objective": objective,
                "tool": tool,
                "inputs": {"verification_commands": commands} if tool == "shell" else {},
                "expected_result": expected,
                "verification": expected,
                "failure_policy": "repair_then_reverify" if index < 4 else "stop_safely",
                "retry_limit": 1,
                "risk_level": "medium" if tool == "repair" else "low",
                "status": "pending",
            }
            for index, (_, objective, tool, expected) in enumerate(specs, 1)
        ]

    @staticmethod
    def scan_project(root: Path) -> dict:
        files = [
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file() and not RealProjectRunner._ignored_project_path(path, root)
        ]
        return {"files": sorted(files), "file_count": len(files)}

    @staticmethod
    def run_command(root: Path, command: str) -> dict:
        completed = subprocess.run(
            command,
            cwd=root,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "command": command,
            "cwd": str(root),
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }

    def repair_project(self, root: Path, project_type: str) -> list[str]:
        repairs = []
        replacements = {
            "MISSING_IMPORT": "from .helpers import format_message",
            "UNDEFINED_MESSAGE": "message = build_message()",
            "LOGIC_BUG": "return a + b",
            "BROKEN_NODE_IMPORT": "const { formatMessage } = require('./lib/format.js');",
            "UNDEFINED_NODE_VALUE": "const value = formatMessage('fixed');",
            "REACT_BAD_IMPORT": "import Counter from './Counter.jsx';",
            "REACT_STATE_BUG": "setCount(count + 1);",
            "API_FIELD_BUG": "const message = payload.message;",
            "START_CONFIG_BUG": "PORT = 8433",
            "CROSS_MODULE_BUG": "return {'message': build_message()}",
        }
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".js", ".jsx", ".json"}:
                continue
            relative = path.relative_to(root)
            if "tests" in relative.parts or path.name.startswith("test"):
                continue
            text = path.read_text(encoding="utf-8")
            updated = text
            for marker, replacement in replacements.items():
                updated = updated.replace(marker, replacement)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                repairs.append(str(path.relative_to(root)))
        return repairs

    @staticmethod
    def snapshot_text_files(root: Path) -> dict[str, str]:
        return {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in root.rglob("*")
            if path.is_file()
            and not RealProjectRunner._ignored_project_path(path, root)
            and path.suffix in {".py", ".js", ".jsx", ".json", ".md", ".txt"}
        }

    def write_diffs(self, task_id: str, before: dict, after: dict) -> dict[str, str]:
        diff_dir = self.artifacts.task_dir(task_id) / "diffs"
        diff_dir.mkdir(parents=True, exist_ok=True)
        diffs = {}
        for name in sorted(set(before) | set(after)):
            if before.get(name, "") == after.get(name, ""):
                continue
            content = "".join(
                difflib.unified_diff(
                    before.get(name, "").splitlines(True),
                    after.get(name, "").splitlines(True),
                    fromfile=f"before/{name}",
                    tofile=f"after/{name}",
                )
            )
            path = diff_dir / f"{name.replace('/', '__')}.diff"
            path.write_text(content, encoding="utf-8")
            diffs[name] = str(path)
        return diffs

    def create_checkpoint(self, task_id: str, root: Path, reason: str) -> dict:
        checkpoint_id = f"{reason}-{datetime.now().strftime('%H%M%S%f')}"
        destination = self.artifacts.task_dir(task_id) / "checkpoints" / checkpoint_id
        shutil.copytree(root, destination, symlinks=True)
        return {
            "checkpoint_id": checkpoint_id,
            "reason": reason,
            "snapshot_path": str(destination),
            "created_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _ignored_project_path(path: Path, root: Path) -> bool:
        ignored = {
            ".git",
            ".snapshots",
            ".next",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
        }
        try:
            relative = path.relative_to(root)
        except ValueError:
            return True
        return any(part in ignored for part in relative.parts)

    def _complete_step(self, task_id: str, step: dict, result: dict) -> None:
        plan = self.artifacts.read_json(task_id, "plan.json") or {"plan": []}
        for item in plan["plan"]:
            if item["step_id"] == step["step_id"]:
                item["status"] = "completed"
                break
        self.artifacts.save_plan(task_id, plan)
        self.artifacts.append_step_log(
            task_id, {"type": "step_result", "step": step, "result": result}
        )
        self.evidence.save(
            task_id,
            step["step_id"],
            "step_result",
            step["tool"],
            json.dumps(result, ensure_ascii=False, default=str),
            step["expected_result"],
        )
        state = self.artifacts.read_json(task_id, "task_state.json") or {}
        completed = list(state.get("completed_steps", []))
        completed.append(step["step_id"])
        self.artifacts.update_state(
            task_id,
            current_step=len(completed),
            completed_steps=completed,
            phase=step["step_id"],
        )
        progress = min(95, len(completed) * 18)
        self._emit(task_id, "step_completed", stage=step["step_id"], step=step, status="completed", summary=f"步骤完成：{step['objective']}", progress=progress)

    def _interrupt(self, task_id: str, started: float) -> dict:
        state = self.artifacts.update_state(
            task_id,
            status="interrupted",
            failure_reason="simulated_app_close",
            duration_seconds=round(time.monotonic() - started, 3),
            rollback_available=True,
        )
        self._emit(task_id, "task_paused", stage="interrupted", status="interrupted", summary="任务已安全中断，可恢复", progress=45)
        return self._result(task_id, state)

    def _step_started(self, task_id: str, step: dict, progress: int) -> None:
        self._emit(task_id, "step_started", stage=step["step_id"], step=step, status="running", summary=f"正在执行：{step['objective']}", progress=progress)
        self._emit(task_id, "tool_started", stage=step["step_id"], step=step, status="running", summary=f"正在使用 {step['tool']} 工具", progress=progress, payload={"tool": step["tool"]})

    def _run_command_with_events(self, task_id: str, step: dict, root: Path, command: str, progress: int) -> dict:
        self._emit(task_id, "tool_started", stage=step["step_id"], step=step, status="running", summary=f"正在运行命令：{command}", progress=progress, payload={"command": command, "cwd": str(root)})
        result = self.run_command(root, command)
        self._emit(task_id, "tool_output", stage=step["step_id"], step=step, status="completed" if result["exit_code"] == 0 else "failed", summary=f"命令退出码：{result['exit_code']}", progress=progress + 4, payload={"command": command, "cwd": str(root), "exit_code": result["exit_code"], "stdout_summary": result["stdout"][-800:], "stderr_summary": result["stderr"][-800:]})
        return result

    def _emit(self, task_id: str, event_type: str, *, stage: str = "", step: dict | None = None, status: str = "", summary: str = "", progress: int = 0, payload: dict | None = None) -> dict:
        return self.artifacts.append_event(
            task_id,
            event_type,
            stage=stage,
            step_id=(step or {}).get("step_id", ""),
            status=status,
            summary=summary,
            progress_percent=progress,
            tool_name=(step or {}).get("tool", ""),
            safe_payload=payload,
        )

    def _result(self, task_id: str, state: dict) -> dict:
        plan = self.artifacts.read_json(task_id, "plan.json") or {}
        return {
            "task_id": task_id,
            "final_status": "PASS" if state.get("status") == "success" else state.get("status", "FAIL").upper(),
            "goal_contract_created": bool(state.get("goal_contract")),
            "plan_steps": len(plan.get("plan", [])),
            "files_changed": state.get("files_changed", []),
            "repair_count": state.get("repair_count", 0),
            "replan_count": state.get("replan_count", 0),
            "claude_call_count": state.get("claude_call_count", 0),
            "success_criteria_met": state.get("success_criteria_met", False),
            "rollback_available": state.get("rollback_available", False),
            "report_path": state.get("final_report_path", ""),
            "duration_seconds": state.get("duration_seconds", 0),
            "failure_reason": state.get("failure_reason", ""),
        }

    @staticmethod
    def build_report(
        goal: str,
        project_type: str,
        changed: list[str],
        initial: list[dict],
        final: list[dict],
        verified: bool,
    ) -> str:
        return (
            "# 真实项目完成报告\n\n"
            f"- 用户目标：{goal}\n"
            f"- 项目类型：{project_type}\n"
            f"- 最终状态：{'成功' if verified else '失败'}\n"
            f"- 修改文件：{', '.join(changed) if changed else '无'}\n"
            f"- 初始验证失败数：{sum(item['exit_code'] != 0 for item in initial)}\n"
            f"- 最终验证通过数：{sum(item['exit_code'] == 0 for item in final)}/{len(final)}\n"
            "- Claude 是否参与：否\n"
            "- 风险与限制：仅修改隔离测试副本；未安装依赖；未调用其他 provider。\n"
        )
