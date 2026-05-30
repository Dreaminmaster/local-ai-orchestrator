# Skill SDK

A Skill is a tool module with a unified interface.

```python
class Skill:
    name: str
    description: str
    capabilities: list[str]
    risk_level: RiskLevel

    async def can_handle(self, task, state) -> bool: ...
    async def execute(self, instruction, context) -> SkillResult: ...
    async def verify(self, result, context) -> VerificationResult: ...
```

## SkillResult

```json
{
  "skill": "browser",
  "success": true,
  "result": "Page opened",
  "evidence": ["screenshot.png"],
  "error": null,
  "needs_follow_up": false,
  "suggested_next_action": "extract_page_text"
}
```

## Built-in Skills

- Shell Skill
- File Skill
- Browser Skill
- Desktop Skill
- External AI Skill
- Search Skill
- Visual Review Skill
- Self Verify Skill

## Skill Chain Examples

- Visual review = Browser screenshot → Visual Review → Self Verify
- Code repair = Shell run → External AI/Codex advice → File modify → Shell rerun → Self Verify
- Research = Search → Browser extract → External AI analysis → Reporter
