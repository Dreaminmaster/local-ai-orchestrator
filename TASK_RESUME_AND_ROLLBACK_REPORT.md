# Task Resume And Rollback Report

## Result

- Interrupted task resume: PASS
- Completed-step duplication check: PASS
- Checkpoint creation: PASS
- Rollback: PASS
- External AI calls during tests: 0

## Resume

Python and mixed-project cases were intentionally interrupted after initial
verification. Their durable task directories retained `task_state.json`,
`goal_contract.json`, `plan.json`, step logs, and checkpoints. Resume continued
from the persisted step, repaired the project, reverified it, and generated the
final report without repeating completed steps.

The frontend Resume action now detects interrupted real-project tasks and calls
`POST /api/tasks/{task_id}/resume-real-project`.

## Rollback

Each task creates a `task_start` checkpoint and an `after_repair` checkpoint. The
Node case exercised rollback successfully. Rollback only replaces the explicitly
configured isolated test project and does not touch directories outside it.

Available APIs:

- `GET /api/tasks/{task_id}/checkpoints`
- `POST /api/tasks/{task_id}/rollback`
- `POST /api/tasks/{task_id}/resume-real-project`

## Known Boundary

This is a local copied-project safety mechanism, not a general source-control
replacement. User projects should still use Git before broader repair testing.

## Real Project Symlink Fix

The Next.js copy exposed that checkpoint snapshots dereferenced
`node_modules/.bin` symlinks. Checkpoint creation and rollback now preserve
symlinks. Resume, whole-task rollback, and reverify passed on real project copies.
