#!/usr/bin/env python3
"""E2E demo: run a project command and trigger repair flow on failure."""

import asyncio
from backend.core.agent import Agent


async def main():
    goal = {
        "goal_mode": "autonomous",
        "original_input": "运行这个项目，报错自己解决",
        "final_goal": "运行项目并对错误进行自动诊断和修复建议",
        "assumptions": ["安全执行，只做诊断"],
        "success_criteria": ["运行命令产生证据", "失败时生成 repair plan", "输出报告"],
    }
    auth = {
        "authorization_mode": "full_autonomy",
        "granted_capabilities": [
            "read_files",
            "run_shell",
            "ask_external_ai",
            "modify_code",
        ],
        "provided_resources": {"project_path": "."},
        "available_external_ai": [],
        "execution_policy": {
            "ask_during_execution": False,
            "autonomous_retry": True,
            "autonomous_repair": True,
        },
        "user_confirmed_authorization": True,
    }
    async for ev in Agent().run_with_contracts(goal, auth):
        print(ev.to_json())


if __name__ == "__main__":
    asyncio.run(main())
