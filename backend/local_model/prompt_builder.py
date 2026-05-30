class ContractScopedPromptBuilder:
    def build_planner_prompt(self, context: dict, output_schema: dict) -> str:
        return f"""你是 local-ai-orchestrator 的任务规划器。只规划当前最必要的少量步骤，不要长篇解释，只输出 JSON。
Goal Contract:\n{context['goal_contract']}\nAuthorization Contract:\n{context['authorization_contract']}\n当前步骤:\n{context['current_step']}\n状态摘要:\n{context['state_summary']}\n相关证据:\n{context['relevant_evidence']}\n可用 Skills:\n{context['available_skills']}\n输出 JSON schema:\n{output_schema}"""
    def build_verifier_prompt(self, context: dict, output_schema: dict) -> str:
        return f"""你是验证器。只判断当前结果是否满足 Goal Contract 的成功标准，不要重新规划。\nGoal Contract:\n{context['goal_contract']}\n当前步骤:\n{context['current_step']}\n相关证据:\n{context['relevant_evidence']}\n只输出 JSON:\n{output_schema}"""
    def build_failure_prompt(self, context: dict, error: str, output_schema: dict) -> str:
        return f"""你是失败诊断器。只判断失败类型和下一步补救方式。\n错误信息:\n{error}\nGoal Contract:\n{context['goal_contract']}\nAuthorization Contract:\n{context['authorization_contract']}\n当前步骤:\n{context['current_step']}\n相关证据:\n{context['relevant_evidence']}\n只输出 JSON:\n{output_schema}"""
