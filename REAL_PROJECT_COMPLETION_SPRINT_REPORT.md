# Real Project Completion Sprint Report

## Result

- Sprint status: PASS
- Real-project matrix: 4/4 PASS
- Actual Claude calls: 0
- Repair matrix: 10/10 PASS
- Focused unit tests: 25 PASS
- Health check: PASS
- Beta validation: PASS, live provider tests skipped
- Frontend syntax: PASS

## Real Project Cases

| Case | Type | Result | Changed Files | Resume | Rollback |
|---|---|---|---|---|---|
| A | Python multi-file CLI | PASS | `app/cli.py`, `app/core.py` | PASS | available |
| B | Node project | PASS | `index.js` | not required | PASS |
| C | React-like frontend | PASS | `src/App.jsx`, `src/Counter.jsx` | not required | available |
| D | Mixed Python/JS | PASS | `backend/config.py`, `backend/service.py`, `frontend/app.js` | PASS | available |

Every case created a Goal Contract, a five-step plan, command evidence, before/after
diffs, checkpoints, and `final_report.md`. All final verification commands exited
with code 0.

## Implemented Completion Loop

`RealProjectRunner` provides a bounded local loop:

1. Inspect the explicit project copy.
2. Build a project-aware Goal Contract and plan.
3. Run initial verification and record stdout/stderr.
4. Apply deterministic repairs with diffs and checkpoints.
5. Re-run verification and generate a durable Chinese report.

The runner never modifies files outside the explicitly supplied project copy and
does not call an external AI provider.

## Product UI

When the user supplies a project path, the main Execute button now calls the
real-project API and renders the Goal Contract, detailed plan, changed files,
verification result, evidence count, and final report. Recent tasks expose report,
plan, changed files, rollback, and resume actions.

The packaged backend/API completed a real Python project task successfully. The
direct automated WebView click path was not instrumented in this sprint, so that
specific automation remains PARTIAL even though the UI code path is connected.

## Remaining Gaps

- Repairs are intentionally deterministic and conservative; arbitrary code repair
  still needs stronger planning or an approved external-AI workflow.
- Direct packaged WebView click automation remains incomplete.
- Checkpoint retention and task-history cleanup policies still need product design.
- Rollback is limited to isolated task copies and should remain so by default.

## Recommendation

The local product core is ready for controlled real-user project testing on copied
projects. The next phase should expand safe repair coverage and verification
strategies before increasing external-AI autonomy.

## Final Product Usability Follow-up

- Two real user project copies passed without modifying their originals.
- The real-project UI now previews and confirms Goal Contracts before execution.
- Standard authorization blocks unconfirmed writes.
- Checkpoint and rollback preserve project symlinks.
- Browser frontend click flow passed; packaged WebView direct click automation
  remains the only partial item.
