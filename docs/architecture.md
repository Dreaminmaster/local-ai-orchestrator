# Architecture

## One-line Definition

Local AI Self-Supervised Orchestrator is a local AI execution runtime that uses a local model as the controller and connects external AI, browser, desktop, files, shell, search, visual review, evidence, verification, and failure repair.

## Core Loop

```text
User Task
  → Goal Interpreter
  → Task Planner
  → Capability Gap Detector
  → Skill Router
  → Skill Execution Layer
  → Observer
  → Evidence Board
  → Verifier
  → Failure Handler
  → Supervisor
  → Final Report
```

## State-driven, not flow-driven

The system does not execute a fixed recipe. Every cycle asks:

1. What is the current state?
2. What is the user goal?
3. What is the gap?
4. Which capability/tool can close the gap?
5. Did the action produce evidence?
6. Is the result closer to the goal?

## Main backend modules

- `goal_interpreter.py`: converts vague user intent into structured goal.
- `planner.py`: creates dynamic plans.
- `capability_gap.py`: detects lack of local capability.
- `skill_router.py`: composes skill chains.
- `agent.py`: orchestration loop.
- `observer.py`: state collection.
- `board.py`: evidence storage.
- `verifier.py`: evidence-based completion checking.
- `failure_handler.py`: failure diagnosis and repair.
- `supervisor.py`: stop / continue / ask-user decision.
- `reporter.py`: evidence-based final report.
