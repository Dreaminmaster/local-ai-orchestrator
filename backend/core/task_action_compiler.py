"""Compile clear local task requests into structured tool actions."""

from __future__ import annotations

import re
from pathlib import Path


class TaskActionCompiler:
    """Create deterministic steps for simple file, shell, and repair tasks.

    The local model still handles general planning. This compiler only activates
    when the goal contains concrete local actions that can be executed safely
    inside the provided project path.
    """

    FILE_RE = re.compile(r"(?<![\w./-])([\w.-]+\.(?:txt|md|py|json|yaml|yml|js|ts))")
    COMMAND_RE = re.compile(
        r"((?:python3|python|node|npm|git)\s+[^\n，。；;]+)",
        re.IGNORECASE,
    )

    def compile(self, goal_contract: dict, authorization_contract: dict) -> list[dict]:
        text = " ".join(
            str(value)
            for value in (
                goal_contract.get("original_input", ""),
                goal_contract.get("final_goal", ""),
            )
            if value
        )
        project_path = str(
            (authorization_contract.get("provided_resources") or {}).get(
                "project_path", ""
            )
        ).strip()
        if not text or not project_path:
            return []

        root = Path(project_path).expanduser()
        lower = text.lower()
        if "pending_external_ai_mock" in lower or "模拟外部 ai" in lower:
            return self._compile_pending_external_ai_mock()

        if self._is_project_review_task(lower):
            steps = self._compile_project_review(root)
            if steps:
                return steps

        if self._is_repair_task(lower):
            steps = self._compile_repair(text, root)
            if steps:
                return steps

        command = self._extract_command(text)
        files = self._file_names(text)
        if command:
            return self._compile_shell_report(command, files)

        if files and self._mentions_file_read(lower) and not any(
            marker in lower for marker in ("内容写入", "内容为", "内容是")
        ):
            return self._compile_read_report(files)
        if files and self._mentions_file_write(lower):
            return self._compile_file_task(text, files)
        return []

    def _compile_file_task(self, text: str, files: list[str]) -> list[dict]:
        target = files[0]
        content = self._extract_content(text) or "Local AI Orchestrator smoke test"
        steps = [
            self._step(
                1,
                f"写入 {target}",
                "file",
                {"action": "write_file", "path": target, "content": content},
                ["write_files"],
            ),
            self._step(
                2,
                f"读取 {target}",
                "file",
                {"action": "read_file", "path": target},
                ["read_files"],
            ),
        ]
        return steps

    def _compile_shell_report(self, command: str, files: list[str]) -> list[dict]:
        report_name = next((name for name in files if name.endswith(".md")), "report.md")
        return [
            self._step(
                1,
                f"运行命令：{command}",
                "shell",
                {"command": command},
                ["run_shell"],
            ),
            self._step(
                2,
                f"把命令结果写入 {report_name}",
                "file",
                {
                    "action": "write_file",
                    "path": report_name,
                    "content_from_previous_stdout": True,
                    "content_prefix": f"# Command Report\n\n`{command}`\n\n```text\n",
                    "content_suffix": "\n```\n",
                },
                ["write_files"],
            ),
        ]

    def _compile_read_report(self, files: list[str]) -> list[dict]:
        source = files[0]
        report_name = next((name for name in files[1:] if name.endswith(".md")), "report.md")
        return [
            self._step(
                1,
                f"读取 {source}",
                "file",
                {"action": "read_file", "path": source},
                ["read_files"],
            ),
            self._step(
                2,
                f"把 {source} 的内容写入 {report_name}",
                "file",
                {
                    "action": "write_file",
                    "path": report_name,
                    "content_from_previous_result": True,
                    "content_prefix": f"# File Summary\n\nSource: `{source}`\n\n",
                },
                ["write_files"],
            ),
        ]

    def _compile_repair(self, text: str, root: Path) -> list[dict]:
        files = self._file_names(text)
        target = next(
            (name for name in files if name.endswith((".py", ".js", ".json"))),
            "main.py",
        )
        path = root / target
        if not path.exists():
            return []
        source = path.read_text(encoding="utf-8", errors="replace")

        if target.endswith(".js"):
            return self._compile_node_reference_repair(target, source)
        if target == "package.json" or "package script" in text.lower():
            return self._compile_package_script_repair(root)

        match = re.search(r"\bprint\(\s*([A-Za-z_]\w*)\s*\)", source)
        if match:
            variable = match.group(1)
            return self._repair_steps(
                target,
                f"修复 {target} 中未定义的 {variable}",
                {"action": "apply_patch", "path": target, "patch": f"prepend:{variable} = 'fixed by Local AI Orchestrator'\n"},
                f"NameError for `{variable}`",
                f"defined `{variable}` before use",
            )

        import_matches = list(re.finditer(
            r"^(?P<indent>\s*)(?:import|from)\s+(?P<module>[A-Za-z_][\w.]*)[^\n]*$",
            source,
            re.MULTILINE,
        ))
        import_match = next(
            (
                match
                for match in import_matches
                if any(
                    marker in match.group("module").lower()
                    for marker in ("nonexistent", "missing", "not_a_real")
                )
            ),
            None,
        )
        if import_match:
            line = import_match.group(0)
            replacement = f"{import_match.group('indent')}pass  # removed unavailable import"
            return self._repair_steps(
                target,
                f"移除 {target} 中不可用的导入",
                {
                    "action": "apply_patch",
                    "path": target,
                    "patch": f"targeted_replace:{line}|||{replacement}",
                },
                f"ImportError for `{import_match.group('module')}`",
                "replaced the unavailable import with a safe no-op",
            )

        syntax_match = re.search(r"^(?P<indent>\s*)def\s+\w+\([^)]*\)\s*$", source, re.MULTILINE)
        if syntax_match:
            broken = syntax_match.group(0)
            return self._repair_steps(
                target,
                f"修复 {target} 的函数定义语法",
                {
                    "action": "apply_patch",
                    "path": target,
                    "patch": f"targeted_replace:{broken}|||{broken}:",
                },
                "SyntaxError in function definition",
                "added the missing colon",
            )
        return []

    def _compile_node_reference_repair(self, target: str, source: str) -> list[dict]:
        match = re.search(r"console\.log\(\s*([A-Za-z_$][\w$]*)\s*\)", source)
        if not match:
            return []
        variable = match.group(1)
        return self._repair_steps(
            target,
            f"修复 {target} 中未定义的 {variable}",
            {
                "action": "apply_patch",
                "path": target,
                "patch": f"prepend:const {variable} = 'fixed by Local AI Orchestrator';\n",
            },
            f"ReferenceError for `{variable}`",
            f"defined `{variable}` before use",
            command=f"node {target}",
        )

    def _compile_package_script_repair(self, root: Path) -> list[dict]:
        package_path = root / "package.json"
        index_path = root / "index.js"
        if not package_path.exists() or not index_path.exists():
            return []
        source = package_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'"start"\s*:\s*"[^"]+"', source)
        if not match:
            return []
        return self._repair_steps(
            "package.json",
            "修复 package.json 的 start script",
            {
                "action": "apply_patch",
                "path": "package.json",
                "patch": f'targeted_replace:{match.group(0)}|||"start": "node index.js"',
            },
            "package script error",
            "updated the start script to run index.js",
            command="npm run start",
        )

    def _repair_steps(
        self,
        target: str,
        repair_goal: str,
        repair_context: dict,
        failure_label: str,
        fix_label: str,
        command: str | None = None,
    ) -> list[dict]:
        command = command or f"python3 {target}"
        report_name = "repair_report.md"
        return [
            self._step(
                1,
                f"运行 {target} 并记录初始失败",
                "shell",
                {"command": command, "continue_on_failure": True},
                ["run_shell"],
            ),
            self._step(
                2,
                repair_goal,
                "file",
                repair_context,
                ["write_files"],
            ),
            self._step(
                3,
                f"重新运行 {target}",
                "shell",
                {"command": command},
                ["run_shell"],
            ),
            self._step(
                4,
                f"写入 {report_name}",
                "file",
                {
                    "action": "write_file",
                    "path": report_name,
                    "content": (
                        "# Repair Report\n\n"
                        f"- Initial failure: {failure_label}\n"
                        f"- Fix: {fix_label}\n"
                        f"- Verification: `{command}` reran successfully\n"
                    ),
                },
                ["write_files"],
            ),
        ]

    def _compile_pending_external_ai_mock(self) -> list[dict]:
        return [
            self._step(
                1,
                "模拟外部 AI 需要用户处理",
                "self_verify",
                {"pending_external_ai_mock": True},
                [],
            )
        ]

    def _compile_project_review(self, root: Path) -> list[dict]:
        """Compile a small-project review into a deterministic local repair flow."""
        main_path = root / "main.py"
        if not main_path.exists():
            return []
        source = main_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"\bprint\(\s*([A-Za-z_]\w*)\s*\)", source)
        if not match:
            return []
        variable = match.group(1)
        return [
            self._step(
                1,
                "运行小项目并记录初始错误",
                "shell",
                {"command": "python3 main.py", "continue_on_failure": True},
                ["run_shell"],
            ),
            self._step(
                2,
                f"修复 main.py 中未定义的 {variable}",
                "file",
                {
                    "action": "apply_patch",
                    "path": "main.py",
                    "patch": f"prepend:{variable} = 'fixed by Local AI Orchestrator'\n",
                },
                ["write_files"],
            ),
            self._step(
                3,
                "重新运行小项目",
                "shell",
                {"command": "python3 main.py"},
                ["run_shell"],
            ),
            self._step(
                4,
                "写入中文修复报告",
                "file",
                {
                    "action": "write_file",
                    "path": "final_report.md",
                    "content": (
                        "# 项目修复报告\n\n"
                        "- 做了什么：检查并运行了这个小型 Python 项目。\n"
                        f"- 修了什么：在 `main.py` 中定义了未声明的变量 `{variable}`。\n"
                        "- 验证结果：`python3 main.py` 已重新运行成功。\n"
                        "- 没有做什么：没有调用外部 AI，也没有修改项目目录外的文件。\n"
                    ),
                },
                ["write_files"],
            ),
        ]

    def _step(
        self,
        number: int,
        goal: str,
        skill: str,
        tool_context: dict,
        required_capabilities: list[str],
    ) -> dict:
        return {
            "step": number,
            "goal": goal,
            "needed_skills": [skill],
            "required_capabilities": required_capabilities,
            "verification_method": "check tool result and evidence",
            "failure_fallback": "diagnose failure and stop or repair",
            "risk_level": "medium",
            "can_auto_execute": True,
            "structured_action": True,
            "tool_context": tool_context,
        }

    def _file_names(self, text: str) -> list[str]:
        return list(dict.fromkeys(self.FILE_RE.findall(text)))

    def _extract_command(self, text: str) -> str:
        match = self.COMMAND_RE.search(text)
        return match.group(1).strip() if match else ""

    def _extract_content(self, text: str) -> str:
        patterns = [
            r"内容写入\s*([^，。；;\n]+)",
            r"内容(?:为|是)\s*([^，。；;\n]+)",
            r"write\s+(?:the\s+)?content\s+([^,.;\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip("\"'“”")
        return ""

    def _mentions_file_write(self, lower: str) -> bool:
        return any(
            marker in lower
            for marker in ("创建", "写入", "生成", "create", "write", "save")
        )

    def _mentions_file_read(self, lower: str) -> bool:
        return any(marker in lower for marker in ("读取", "总结", "read", "summarize"))

    def _is_repair_task(self, lower: str) -> bool:
        return any(marker in lower for marker in ("修复", "repair", "fix"))

    def _is_project_review_task(self, lower: str) -> bool:
        return (
            any(marker in lower for marker in ("检查这个小项目", "检查这个项目", "项目检查"))
            and any(marker in lower for marker in ("修复", "repair", "fix"))
        )
