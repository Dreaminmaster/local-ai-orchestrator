# Architecture

## Current core architecture

```text
User Task
↓
Goal Strategy
  - Clarify First
  - Autonomous Goal
↓
Goal Contract
↓
Authorization Strategy
  - Standard Authorization
  - Full Autonomy Authorization
↓
Authorization Contract
↓
Local Model Optimization Layer
  - Context Window Manager
  - Prompt Builder
  - JSON Repair Parser
  - Step State Manager
  - Evidence Retriever
  - Tool Result Summarizer
  - External AI Escalation Router
  - Prompt Profiles
  - Model Capability Registry
  - Retry Policy
↓
Planner / Skill Router / Verifier / Failure Handler
↓
Skill Execution
↓
Evidence Board
↓
Reporter
```

## Product principle

Full Autonomy is not a goal-understanding mode. It is an execution authorization strategy.

The system is designed for weak local models. The local model is not the expert. It is the controller that makes small current-step judgments while the system stores state, retrieves evidence, summarizes tool results, repairs JSON, retries, and escalates to stronger tools or external AI when needed.
