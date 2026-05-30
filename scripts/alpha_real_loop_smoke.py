#!/usr/bin/env python3
"""Alpha real-loop smoke tests.
These are safe structural tests that validate the runtime path without requiring real external logins.
"""
from pathlib import Path
import asyncio
from backend.core.agent import Agent
from backend.local_model.json_repair import JSONRepairParser

async def test_full_autonomy_chain():
    goal={"goal_mode":"autonomous","original_input":"帮我检查这个仓库下一步还差什么","final_goal":"检查仓库下一步缺口并输出报告","assumptions":["只做安全检查"],"success_criteria":["生成计划","保存证据","生成报告"],"completion_standard":"有报告"}
    auth={"authorization_mode":"full_autonomy","granted_capabilities":["read_files","ask_external_ai","take_screenshots"],"provided_resources":{"project_path":"."},"available_external_ai":[],"execution_policy":{"ask_during_execution":False,"autonomous_retry":True,"autonomous_repair":True},"user_confirmed_authorization":True}
    events=[]
    async for ev in Agent().run_with_contracts(goal, auth):
        events.append(ev.type)
        if len(events)>20: break
    assert "goal_contract" in events and "authorization_contract" in events and "plan" in events
    print("OK full autonomy structural chain", events[:8])

def test_json_repair():
    parsed=JSONRepairParser().parse('解释```json\n{“ok”：true，}\n```')
    assert parsed.get('ok') is True
    print("OK json repair")

async def main():
    test_json_repair()
    await test_full_autonomy_chain()

if __name__ == '__main__':
    asyncio.run(main())
