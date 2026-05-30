"""Capability Gap Detector — Identify when the local model needs help."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


SYSTEM_PROMPT = """你是一个能力缺口检测器。你的任务是判断当前步骤是否超出本地模型的能力范围。

你必须输出严格的 JSON 格式：
{
  "current_problem": "当前要解决的问题",
  "local_model_can_handle": true/false,
  "confidence": 0.8,
  "gap_type": "none/code_gap/visual_gap/factual_gap/execution_gap/planning_gap/preference_gap/verification_gap",
  "recommended_help": [
    {
      "tool": "技能名称",
      "target": "具体目标（如 ChatGPT、Claude）",
      "reason": "为什么需要这个帮助"
    }
  ]
}

能力缺口类型：
- none: 本地模型可以处理
- code_gap: 代码能力不足
- visual_gap: 视觉判断不足
- factual_gap: 事实信息不足
- execution_gap: 执行能力不足
- planning_gap: 规划不确定
- preference_gap: 用户偏好不明确
- verification_gap: 无法确认是否完成

判断标准：
1. 如果需要审美判断 → visual_gap → 推荐视觉模型
2. 如果需要复杂代码 → code_gap → 推荐 Codex/Claude
3. 如果需要最新信息 → factual_gap → 推荐搜索
4. 如果需要操作电脑 → execution_gap → 推荐桌面/浏览器技能
5. 如果不确定方案 → planning_gap → 推荐多模型对比"""


class CapabilityGapDetector:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def detect(self, step: dict, state: dict) -> dict:
        """Detect capability gaps for the current step."""
        context = f"""当前步骤：
{json.dumps(step, ensure_ascii=False, indent=2)}

当前状态：
{json.dumps(state, ensure_ascii=False, indent=2)}"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        try:
            result = await self.llm.chat_json(messages, temperature=0.2)
            result.setdefault("local_model_can_handle", True)
            result.setdefault("gap_type", "none")
            result.setdefault("recommended_help", [])
            result["requires_help"] = not result["local_model_can_handle"]
            return result
        except Exception as e:
            return {
                "current_problem": step.get("goal", ""),
                "local_model_can_handle": True,
                "confidence": 0.5,
                "gap_type": "none",
                "recommended_help": [],
                "requires_help": False,
                "error": str(e),
            }
