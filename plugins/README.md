# Plugin SDK

自定义 Skill 需要继承 `backend.skills.base.Skill`：

```python
from backend.skills.base import Skill, SkillResult, RiskLevel

class MySkill(Skill):
    name = "my_skill"
    description = "My custom skill"
    capabilities = ["do_something"]
    risk_level = RiskLevel.LOW

    async def can_handle(self, task, state) -> bool:
        return "something" in task.get("description", "")

    async def execute(self, instruction, context) -> SkillResult:
        return SkillResult(
            skill=self.name,
            success=True,
            result="done",
        )
```

当前版本插件自动加载尚未实现，可先在 `SkillRouter` 中注册。
