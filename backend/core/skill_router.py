"""Skill Router — Select the best skill chain for a task step."""
from __future__ import annotations
from backend.skills.base import Skill
from backend.skills.shell_skill import ShellSkill
from backend.skills.file_skill import FileSkill
from backend.skills.browser_skill import BrowserSkill
from backend.skills.desktop_skill import DesktopSkill
from backend.skills.external_ai_skill import ExternalAISkill
from backend.skills.search_skill import SearchSkill
from backend.skills.visual_review_skill import VisualReviewSkill
from backend.skills.self_verify_skill import SelfVerifySkill


class SkillRouter:
    """Routes tasks to the appropriate skill chain."""

    def __init__(self):
        self.skills: dict[str, Skill] = {
            "shell": ShellSkill(),
            "file": FileSkill(),
            "browser": BrowserSkill(),
            "desktop": DesktopSkill(),
            "external_ai": ExternalAISkill(),
            "search": SearchSkill(),
            "visual_review": VisualReviewSkill(),
            "self_verify": SelfVerifySkill(),
        }

    def get_skill(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def get_all_skills(self) -> dict[str, Skill]:
        return self.skills

    def select(self, step: dict, gap: dict | None = None) -> list[str]:
        """Select skill chain for a step, considering capability gaps."""
        needed = step.get("needed_skills", [])

        # If there's a capability gap, add recommended tools
        if gap and gap.get("requires_help"):
            for rec in gap.get("recommended_help", []):
                tool = rec.get("tool", "")
                # Map tool names to skill names
                skill_name = tool.replace("_skill", "")
                if skill_name in self.skills and skill_name not in needed:
                    needed.append(skill_name)

        # Filter to available skills
        chain = [s for s in needed if s in self.skills]

        # Always add self_verify at the end if not present
        if "self_verify" not in chain:
            chain.append("self_verify")

        return chain

    async def execute_chain(self, chain: list[str], instruction: str, context: dict) -> list[dict]:
        """Execute a chain of skills sequentially."""
        results = []
        current_context = dict(context)

        for skill_name in chain:
            skill = self.skills.get(skill_name)
            if not skill:
                results.append({
                    "skill": skill_name,
                    "success": False,
                    "error": f"Skill not found: {skill_name}",
                })
                continue

            result = await skill.execute(instruction, current_context)
            results.append(result.to_dict())

            # Pass result to next skill's context
            current_context["previous_result"] = result.to_dict()
            if result.evidence:
                current_context.setdefault("evidence", []).extend(result.evidence)

            # Stop chain if a critical skill fails
            if not result.success and skill_name != "self_verify":
                break

        return results
