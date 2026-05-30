"""Skills API — List and manage available skills."""
from __future__ import annotations
from fastapi import APIRouter
from backend.core.skill_router import SkillRouter

router = APIRouter(tags=["skills"])

skill_router = SkillRouter()


@router.get("/skills")
async def list_skills():
    """List all available skills with their capabilities."""
    skills = skill_router.get_all_skills()
    result = []
    for name, skill in skills.items():
        result.append({
            "name": name,
            "description": skill.description,
            "capabilities": skill.capabilities,
            "risk_level": skill.risk_level.value if hasattr(skill.risk_level, 'value') else skill.risk_level,
        })
    return {"skills": result}
