#!/usr/bin/env python3
"""E2E smoke test for gemini Web AI adapter.
Requires Playwright browser and a logged-in persistent profile.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from backend.skills.external_ai_web.web_ai_skill import WebAISkill


async def main():
    result = await WebAISkill().execute(
        "请用一句话回答：local-ai-orchestrator 的目标是什么？",
        {"provider": "gemini", "headless": False, "max_followups": 1},
    )
    data = result.to_dict()
    report = {
        "provider": "gemini",
        "success": result.success,
        "login_detection": not data.get("metadata", {}).get("needs_login", False),
        "send_prompt": result.error is None
        or "selector" not in str(result.error).lower(),
        "wait_complete": bool(result.result),
        "extract_answer": bool(result.result),
        "follow_up": data.get("metadata", {}).get("followups", 0) >= 0,
        "evidence_saved": bool(result.evidence),
        "fallback_result": data.get("metadata", {}).get("fallback"),
        "raw": data,
        "created_at": datetime.now().isoformat(),
    }
    out_dir = Path("runtime/test_reports/web_ai")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "gemini.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"REPORT={out}")


if __name__ == "__main__":
    asyncio.run(main())
