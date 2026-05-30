# Contract Runtime Upgrade

This document describes the second-stage implementation beyond the initial two-dimensional skeleton.

## Implemented

### Clarification Session

Files:

- `backend/schemas/clarification_session.py`
- `backend/core/clarification_session.py`

Behavior:

- `POST /api/task/prepare-goal` returns `needs_clarification=true` in `clarify_first` mode.
- The frontend displays/collects answers and calls `POST /api/task/confirm-goal`.
- Evidence types `clarification_question` and `clarification_answer` are recorded.

### Contract WebSocket

Files:

- `backend/api/websocket.py`
- `frontend/app.js`

Endpoint:

```text
/ws/execute-contract
```

The frontend now uses WebSocket streaming as the primary execution path and keeps REST `/api/task/start` as fallback.

### Authorization + Confirmation Queue

Files:

- `backend/confirmation/action_risk_classifier.py`
- `backend/core/skill_router.py`

Behavior:

- Standard authorization: risky concrete actions create confirmation requests.
- Full autonomy: actions execute if capabilities are granted and are recorded as `autonomous_action` evidence.

### Dynamic Full Autonomy Preflight

Files:

- `backend/core/dynamic_preflight.py`
- `backend/api/contracts.py`
- `frontend/app.js`

Behavior:

- Preflight is generated from `user_input + goal_contract`.
- Returns `required_capabilities`, `required_resources`, `recommended_external_ai`, and `preflight_questions`.
- Frontend renders capability checkboxes dynamically.

### Planner / Verifier / Failure Handler Contract Integration

Files:

- `backend/core/planner.py`
- `backend/core/verifier.py`
- `backend/core/failure_taxonomy.py`
- `backend/core/repair_planner.py`
- `backend/core/failure_handler.py`

Behavior:

- Planner prompt includes `required_capabilities`, `verification_method`, and `failure_fallback`.
- Verifier exposes `check_with_contracts` and checks `success_criteria`.
- Failure handler distinguishes: `goal_unclear`, `authorization_missing`, `resource_missing`, `selector_failed`, `external_ai_failed`, `visual_quality_failed`, `code_failed`.

## Execution combinations

All four combinations are supported through Contract generation:

1. `clarify_first + standard`
2. `clarify_first + full_autonomy`
3. `autonomous + standard`
4. `autonomous + full_autonomy`

## Remaining production work

- Replace prompt-based clarification popup with a full in-page multi-turn panel.
- Persist Clarification Session in SQLite rather than in-memory store.
- Connect Confirmation Queue UI to real-time approval/rejection.
- Harden selectors for external AI web pages.
- Add real vision-model-backed desktop target localization.
