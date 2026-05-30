class VisualPromptBuilder:
    def build_review(self, goal: str) -> str:
        return f"""请以严格 JSON 评价界面。目标：{goal}
维度：高级感、低端模板感、字体、间距、颜色、布局、真实感、交互清晰度。
返回字段：overall_score,is_premium,has_template_feel,problems,improvements,css_suggestions,pass_gate。"""

    def build_comparison(self, goal: str) -> str:
        return f"""比较修改前后截图是否更接近目标：{goal}。输出 improved,before_score,after_score,regressions,next_suggestions。"""
