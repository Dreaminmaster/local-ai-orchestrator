"""Reporter — Generate final task reports."""
from __future__ import annotations
import json
from backend.llm.base import LLMProvider, LLMMessage


SYSTEM_PROMPT = """你是一个任务报告生成器。根据任务执行过程生成完整的最终报告。

报告必须包含：
1. 任务摘要
2. 执行了什么操作
3. 为什么这么做
4. 问了哪些外部 AI
5. 遇到了哪些问题
6. 怎么解决的
7. 修改了哪些文件
8. 用了哪些证据判断完成
9. 哪些地方已经验证
10. 哪些地方仍然不确定

输出格式为 Markdown。"""


class Reporter:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate(self, task: dict, steps: list[dict], evidence: list[dict]) -> str:
        """Generate a final report for the task."""
        context = f"""任务信息：
{json.dumps(task, ensure_ascii=False, indent=2)}

执行步骤：
{json.dumps(steps, ensure_ascii=False, indent=2)}

证据：
{json.dumps(evidence, ensure_ascii=False, indent=2)}"""

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"请为以下任务生成最终报告：\n\n{context}"),
        ]

        try:
            resp = await self.llm.chat(messages, temperature=0.3)
            return resp.content
        except Exception as e:
            # Fallback: simple report
            return self._fallback_report(task, steps, evidence)

    def _fallback_report(self, task: dict, steps: list[dict], evidence: list[dict]) -> str:
        """Generate a simple report without LLM."""
        lines = [
            f"# 任务报告",
            f"",
            f"## 任务目标",
            f"{task.get('goal', task.get('main_goal', 'N/A'))}",
            f"",
            f"## 执行步骤",
        ]

        for i, step in enumerate(steps, 1):
            status = "✅" if step.get("success", step.get("status") == "completed") else "❌"
            desc = step.get("description", step.get("goal", "N/A"))
            lines.append(f"{i}. {status} {desc}")

        lines.extend([
            f"",
            f"## 证据",
        ])

        for ev in evidence:
            lines.append(f"- [{ev.get('type', 'unknown')}] {ev.get('supports', ev.get('content', 'N/A'))}")

        success_count = sum(1 for s in steps if s.get("success", s.get("status") == "completed"))
        lines.extend([
            f"",
            f"## 总结",
            f"共执行 {len(steps)} 步，成功 {success_count} 步。",
        ])

        return "\n".join(lines)
