#!/usr/bin/env python3
"""External AI advice + PatchExtractor → FileSkill repair E2E.

Simulates external AI response with a unified diff. PatchExtractor extracts it,
FileSkill applies it, ShellSkill reruns.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.core.agent import Agent
from backend.core.patch_extractor import PatchExtractor

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/e2e_external_advice.json"

SIMULATED_AI_RESPONSE = """\
代码分析发现 main.py 第 5 行 UNDEFINED_VARIABLE 未定义。
请用以下 diff 修复：

```diff
--- a/main.py
+++ b/main.py
@@ -4,3 +4,3 @@
 def buggy_function():
-    msg = UNDEFINED_VARIABLE
+    msg = 'fixed by external AI advice'
     print(msg)
```
"""


async def run_shell(agent: Agent, command: list[str], cwd: Path):
    return await agent.skill_router.execute_chain(
        ["shell"],
        " ".join(command),
        {
            "command": " ".join(command),
            "cwd": str(cwd),
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["run_shell"],
            },
        },
    )


async def main():
    agent = Agent()
    extractor = PatchExtractor()
    src = ROOT / "tests/fixtures/broken_external_advice_project"
    work = ROOT / "runtime/tmp" / f"external_advice_{uuid4().hex[:8]}"
    shutil.copytree(src, work)

    # 1. Before: run broken project → should fail
    before = await run_shell(agent, ["python3", "main.py"], work)
    before_success = any(r.get("success") for r in before)
    assert not before_success, "Expected before to fail"

    # 2. Extract patches from AI response
    result = extractor.extract(SIMULATED_AI_RESPONSE)
    patches = result.patches
    assert patches, f"Expected at least one patch: {result.summary}"
    assert patches[0].format == "diff"

    # 3. Apply via FileSkill
    file_path = str(work / "main.py")
    patch_str = patches[0].to_file_patch()
    file_apply = await agent.skill_router.execute_chain(
        ["file"],
        patch_str,
        {
            "action": "apply_patch",
            "path": file_path,
            "patch": patch_str,
            "authorization_contract": {
                "authorization_mode": "full_autonomy",
                "granted_capabilities": ["write_files"],
            },
        },
    )
    applied = any(r.get("success") for r in file_apply)
    assert applied, "Expected patch to apply"

    # 4. After: rerun
    after = await run_shell(agent, ["python3", "main.py"], work)
    after_success = any(r.get("success") for r in after)
    assert after_success, "Expected after rerun to succeed"

    report = {
        "created_at": datetime.now().isoformat(),
        "fixture": "broken_external_advice_project",
        "before_success": before_success,
        "after_success": after_success,
        "patches_found": len(patches),
        "patch_format": patches[0].format,
        "hunk_count": patches[0].hunk_count,
        "status": "PASS",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
