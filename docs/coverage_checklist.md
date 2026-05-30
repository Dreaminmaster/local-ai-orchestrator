# Product Design Coverage Checklist

This checklist maps the original product design document to repository implementation.

| Requirement | Status | Location |
|---|---:|---|
| Independent AI task workbench | MVP | `frontend/` |
| Local model connector | Done | `backend/llm/` |
| External AI operator | MVP | `backend/skills/external_ai_skill.py` |
| Desktop control | MVP | `backend/skills/desktop_skill.py` |
| Browser automation | MVP | `backend/skills/browser_skill.py` |
| File / terminal / code tools | MVP | `file_skill.py`, `shell_skill.py`, `codex_skill.py` |
| Memory Skill | MVP | `memory_skill.py`, `memory/` |
| Visual review | MVP | `visual_review_skill.py` |
| Task supervisor | Done | `core/supervisor.py` |
| Evidence board | Done | `evidence/board.py` |
| Failure repair | Done | `core/failure_handler.py` |
| Goal Interpreter | Done | `core/goal_interpreter.py` |
| Task Planner | Done | `core/planner.py` |
| Capability Gap Detector | Done | `core/capability_gap.py` |
| Skill Router | Done | `core/skill_router.py` |
| Observer | Done | `core/observer.py` |
| Verifier | Done | `core/verifier.py` |
| Reporter | Done | `core/reporter.py` |
| SQLite structures | Done | `storage/database.py` |
| User preferences | MVP | `memory/user_preferences.py` |
| Task memory | MVP | `memory/task_memory.py` |
| Risk control | MVP | `security/permissions.py` |
| Snapshots / rollback | MVP | `evidence/snapshot.py` |
| Plugin system | Skeleton | `plugins/README.md` |
| Desktop shell | Planned | `docs/desktop_app.md` |

Legend: Done = implemented in code; MVP = usable first version; Skeleton = extension point; Planned = documented roadmap.
