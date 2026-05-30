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

    async def generate(
        self, task: dict, steps: list[dict], evidence: list[dict]
    ) -> str:
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
        except Exception:
            # Fallback: simple report
            return self._fallback_report(task, steps, evidence)

    async def generate_with_contracts(
        self,
        goal_contract: dict,
        authorization_contract: dict,
        steps: list[dict],
        evidence: list[dict],
    ) -> str:
        """Generate report that separates goal understanding and authorization."""
        context = f"""目标理解部分：
{json.dumps(goal_contract, ensure_ascii=False, indent=2)}

执行授权部分：
{json.dumps(authorization_contract, ensure_ascii=False, indent=2)}

执行过程：
{json.dumps(steps, ensure_ascii=False, indent=2)}

证据：
{json.dumps(evidence, ensure_ascii=False, indent=2)}"""
        prompt = """请生成最终报告，必须分成以下章节：
1. 目标理解：用户原始输入、目标理解策略、是否追问、AI 默认假设、最终目标、成功标准。
2. 执行授权：执行授权策略、已授予能力、已提供资源、使用了哪些外部 AI、是否全自主执行。
3. 本地模型优化过程：是否使用短上下文、JSON 修复、证据检索、工具结果摘要、StepState、外部 AI 升级。
4. 外部 AI 求助：问了谁、为什么问、回答摘要、证据文件。
5. 执行步骤：做了什么、改了什么、运行了什么、遇到什么问题、如何自主修复。
6. 证据：哪些证据证明完成。
7. 未完成项：仍不确定或待人工处理的部分。"""
        try:
            resp = await self.llm.chat(
                [
                    LLMMessage(role="system", content=SYSTEM_PROMPT),
                    LLMMessage(role="user", content=prompt + "\n\n" + context),
                ],
                temperature=0.3,
            )
            return resp.content
        except Exception:
            return self._fallback_contract_report(
                goal_contract, authorization_contract, steps, evidence
            )

    def _fallback_contract_report(
        self,
        goal_contract: dict,
        authorization_contract: dict,
        steps: list[dict],
        evidence: list[dict],
    ) -> str:
        lines = [
            "# 任务报告",
            "",
            "## 目标理解部分",
            f"- 用户原始输入：{goal_contract.get('original_input', '')}",
            f"- 目标理解策略：{goal_contract.get('goal_mode', '')}",
            f"- 最终目标：{goal_contract.get('final_goal', '')}",
            f"- AI 默认假设：{', '.join(goal_contract.get('assumptions', []))}",
            f"- 成功标准：{', '.join(goal_contract.get('success_criteria', []))}",
            "",
            "## 执行授权部分",
            f"- 执行授权策略：{authorization_contract.get('authorization_mode', '')}",
            f"- 已授予能力：{', '.join(authorization_contract.get('granted_capabilities', []))}",
            f"- 已提供资源：{json.dumps(authorization_contract.get('provided_resources', {}), ensure_ascii=False)}",
            f"- 可用外部 AI：{', '.join(authorization_contract.get('available_external_ai', []))}",
            "## 本地模型优化过程",
            "- 已接入 ContextWindowManager / EvidenceRetriever / ToolResultSummarizer / StepState / JSONRepairParser。",
            "",
            "## 外部 AI 求助",
            "- 见证据中 external_ai / web_ai / autonomous_action 条目。",
            "",
            "## 执行过程",
        ]
        for i, step in enumerate(steps, 1):
            status = "✅" if step.get("success") else "❌"
            lines.append(
                f"{i}. {status} {step.get('skill', step.get('goal', 'step'))}: {str(step.get('result', ''))[:160]}"
            )
        lines.extend(["", "## 证据"])
        for ev in evidence:
            lines.append(
                f"- [{ev.get('type', 'unknown')}] {ev.get('supports', ev.get('content', ''))}"
            )
        return "\n".join(lines)

    def _fallback_report(
        self, task: dict, steps: list[dict], evidence: list[dict]
    ) -> str:
        """Generate a simple report without LLM."""
        lines = [
            "# 任务报告",
            "",
            "## 任务目标",
            f"{task.get('goal', task.get('main_goal', 'N/A'))}",
            "",
            "## 执行步骤",
        ]

        for i, step in enumerate(steps, 1):
            status = (
                "✅" if step.get("success", step.get("status") == "completed") else "❌"
            )
            desc = step.get("description", step.get("goal", "N/A"))
            lines.append(f"{i}. {status} {desc}")

        lines.extend(
            [
                "",
                "## 证据",
            ]
        )

        for ev in evidence:
            lines.append(
                f"- [{ev.get('type', 'unknown')}] {ev.get('supports', ev.get('content', 'N/A'))}"
            )

        success_count = sum(
            1 for s in steps if s.get("success", s.get("status") == "completed")
        )
        lines.extend(
            [
                "",
                "## 总结",
                f"共执行 {len(steps)} 步，成功 {success_count} 步。",
            ]
        )

        return "\n".join(lines)
