# Local Model Optimization Layer

This project does not assume the local model is strong.

The local model may have:

- short context
- weak reasoning
- unstable JSON output
- poor long-task memory
- unreliable tool planning
- limited code ability
- no vision capability

So the system does **not** ask the local model to solve a whole complex task at once.

## Principle

```text
Weak local model = current small judgment only
Step State = progress memory
Evidence Board = facts
Goal Contract = target
Authorization Contract = permissions
Tools = execution
External AI = capability supplement
Verifier = evidence-based completion judgment
```

## Architecture

```text
User Task
↓
Goal Contract
↓
Authorization Contract
↓
Local Model Optimization Layer
   ├── Context Window Manager
   ├── Contract-scoped Prompt Builder
   ├── JSON Repair Parser
   ├── Step State Manager
   ├── Evidence Retriever
   ├── Tool Result Summarizer
   ├── External AI Escalation Router
   ├── Prompt Profiles
   ├── Model Capability Registry
   └── Retry Policy
↓
Planner / Skill Router / Verifier / Failure Handler
```

## Implemented files

```text
backend/local_model/context_manager.py
backend/local_model/prompt_builder.py
backend/local_model/json_repair.py
backend/local_model/step_state.py
backend/local_model/evidence_retriever.py
backend/local_model/tool_result_summarizer.py
backend/local_model/external_ai_escalation.py
backend/local_model/prompt_profiles.py
backend/local_model/model_capability.py
backend/local_model/retry_policy.py
```

## Runtime integration

- `LLMProvider.chat_json()` now uses `JSONRepairParser`.
- `Planner` uses local-model-friendly short JSON prompts.
- `Agent.run_with_contracts()` builds optimized context per step.
- `Agent.run_with_contracts()` retrieves only relevant evidence.
- Tool results are summarized before being stored in `all_results`.
- Step progress is stored in `StepStateManager`.
- Failures can trigger `ExternalAIEscalationRouter`.
- Failure taxonomy includes local-model failure types.

## Why this matters

The product's value is not that the local model is omnipotent. The product value is that a weak local model can still complete complex tasks through contracts, state, tools, evidence, fallback, and escalation.
