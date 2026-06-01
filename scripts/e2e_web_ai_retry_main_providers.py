#!/usr/bin/env python3
"""Retry main Web AI providers and record results."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.skills.external_ai_web.web_ai_skill import WebAISkill

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runtime/test_reports/web_ai/main_providers_retry.json"
PROVIDERS = ["claude", "chatgpt"]


async def test(provider):
    result = await WebAISkill().execute(
        "Say hello in one short sentence.",
        {"provider": provider, "headless": False, "max_followups": 0},
    )
    data = result.to_dict()
    return {
        "provider": provider,
        "success": result.success,
        "answer_preview": data.get("result", "")[:200],
        "error": data.get("error", "")[:200],
        "evidence_saved": bool(result.evidence),
        "tested_at": datetime.now().isoformat(),
    }


async def main():
    results = []
    for p in PROVIDERS:
        r = await test(p)
        results.append(r)
        print(r["provider"], "PASS" if r["success"] else "FAIL")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {"created_at": datetime.now().isoformat(), "results": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
