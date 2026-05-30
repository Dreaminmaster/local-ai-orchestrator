from dataclasses import dataclass, field

@dataclass
class VisualReviewResult:
    overall_score: float = 0.0
    is_premium: bool = False
    has_template_feel: bool = True
    problems: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    css_suggestions: list[str] = field(default_factory=list)
    pass_gate: bool = False
