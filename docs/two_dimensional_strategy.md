# Two-dimensional Strategy Revision

The product no longer treats "Full Autonomy" as a peer of goal-confirmation or autonomous-creative modes.

The correct model is:

```text
Goal Understanding Strategy × Execution Authorization Strategy
```

## Dimension 1: Goal Understanding Strategy

- `clarify_first`: Goal confirmation mode. The system asks clarifying questions and establishes the target before execution.
- `autonomous`: Autonomous creative mode. The system infers, expands, and records assumptions.

The output is always a `GoalContract`.

## Dimension 2: Execution Authorization Strategy

- `standard`: Confirm key actions during execution.
- `full_autonomy`: Ask for resources and permissions once before execution, then proceed autonomously within the granted scope.

The output is always an `AuthorizationContract`.

## Four combinations

1. Goal confirmation + standard authorization
2. Goal confirmation + full autonomy authorization
3. Autonomous creative + standard authorization
4. Autonomous creative + full autonomy authorization

The most important target workflow is:

```text
autonomous + full_autonomy
```

## New startup flow

```text
user input
→ choose goal_mode
→ prepare Goal Contract
→ choose authorization_mode
→ preflight if full_autonomy
→ prepare Authorization Contract
→ Agent receives both contracts
→ Planner uses Goal Contract
→ Skill Router uses Authorization Contract
→ Verifier uses Goal Contract
→ Supervisor / Failure Handler use both
→ Reporter separates goal understanding and authorization
```

## New API

- `POST /api/task/prepare-goal`
- `POST /api/task/confirm-goal`
- `GET /api/task/full-autonomy-preflight`
- `POST /api/task/prepare-authorization`
- `POST /api/task/confirm-authorization`
- `POST /api/task/start`

## Main files

- `backend/schemas/goal_contract.py`
- `backend/schemas/authorization_contract.py`
- `backend/core/goal_contract.py`
- `backend/core/authorization_contract.py`
- `backend/core/intent_clarifier.py`
- `backend/core/ask_or_assume.py`
- `backend/core/full_autonomy_preflight.py`
- `backend/api/contracts.py`
- `backend/core/agent.py`
- `backend/core/skill_router.py`
- `backend/core/reporter.py`
- `frontend/index.html`
- `frontend/app.js`
