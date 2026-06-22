# Beta Validation Report

Generated: 2026-06-22T19:38:53.689402

Overall: **PASS**

## Validation Summary

- core_pass: `true`
- workspace_auto_pass: `false`
- workspace_needs_user: `false`
- blocking_failures: `0`
- Workspace needing login/verification is a resumable product state, not a beta kernel failure.

## Portable Mode

- Project root: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`
- venv: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/venv` (missing)
- Playwright browsers: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.playwright-browsers` (exists)
- runtime: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime` (exists)
- PLAYWRIGHT_BROWSERS_PATH expected: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.playwright-browsers`

## Checks

| Check | Status | Command |
|---|---:|---|
| health_check | PASS | `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv/bin/python scripts/health_check.py` |
| repair_matrix | PASS | `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv/bin/python scripts/e2e_agent_driven_repair_matrix.py` |
| frontend_node_check | PASS | `node --check frontend/app.js` |
| claude_extractor_unittest | PASS | `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv/bin/python -m unittest tests/test_claude_answer_extractor_from_evidence.py` |
| live_claude_workspace_e2e | SKIP | `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/.build-venv/bin/python scripts/e2e_claude_workspace_live.py` |

## Repair Matrix

- Latest report summary: 10/10 PASS

## Claude Web Live E2E

- Requested in this run: false
- Default behavior: not run unless `--live-claude` is provided.
- NEED_USER_INTERVENTION means the workspace correctly paused for user login/verification and can resume.

## Details

### health_check

- Status: PASS
- Return code: 0

stdout tail:

```text
OK: repository health check passed

```

stderr tail:

```text

```

### repair_matrix

- Status: PASS
- Return code: 0

stdout tail:

```text

      "rerun_success": true,
      "verification": true,
      "report": true,
      "events": [
        "shell_failed",
        "failure_repair",
        "repair_step_inserted",
        "rerun_success",
        "verification",
        "report"
      ],
      "diagnosis_failure_type": "resource_missing",
      "pass": true
    },
    {
      "fixture": "broken_package_script",
      "before_success": false,
      "after_success": true,
      "shell_failed": true,
      "failure_repair": true,
      "repair_step_inserted": true,
      "file_modified": true,
      "rerun_success": true,
      "verification": true,
      "report": true,
      "events": [
        "shell_failed",
        "failure_repair",
        "repair_step_inserted",
        "rerun_success",
        "verification",
        "report"
      ],
      "diagnosis_failure_type": "resource_missing",
      "pass": true
    },
    {
      "fixture": "broken_python_missing_package",
      "before_success": false,
      "after_success": true,
      "shell_failed": true,
      "failure_repair": true,
      "repair_step_inserted": true,
      "file_modified": true,
      "rerun_success": true,
      "verification": true,
      "report": true,
      "events": [
        "shell_failed",
        "failure_repair",
        "repair_step_inserted",
        "rerun_success",
        "verification",
        "report"
      ],
      "diagnosis_failure_type": "resource_missing",
      "pass": true
    },
    {
      "fixture": "broken_node_missing_package",
      "before_success": false,
      "after_success": true,
      "shell_failed": true,
      "failure_repair": true,
      "repair_step_inserted": true,
      "file_modified": true,
      "rerun_success": true,
      "verification": true,
      "report": true,
      "events": [
        "shell_failed",
        "failure_repair",
        "repair_step_inserted",
        "rerun_success",
        "verification",
        "report"
      ],
      "diagnosis_failure_type": "resource_missing",
      "pass": true
    },
    {
      "fixture": "broken_wrong_package_script",
      "before_success": false,
      "after_success": true,
      "shell_failed": true,
      "failure_repair": true,
      "repair_step_inserted": true,
      "file_modified": true,
      "rerun_success": true,
      "verification": true,
      "report": true,
      "events": [
        "shell_failed",
        "failure_repair",
        "repair_step_inserted",
        "rerun_success",
        "verification",
        "report"
      ],
      "diagnosis_failure_type": "resource_missing",
      "pass": true
    }
  ]
}
broken_python_project: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_node_project: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_python_import: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_python_syntax: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_node_module_not_found: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_node_syntax: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_package_script: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_python_missing_package: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_node_missing_package: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']
broken_wrong_package_script: PASS events=['shell_failed', 'failure_repair', 'repair_step_inserted', 'rerun_success', 'verification', 'report']

```

stderr tail:

```text

```

### frontend_node_check

- Status: PASS
- Return code: 0

stdout tail:

```text

```

stderr tail:

```text

```

### claude_extractor_unittest

- Status: PASS
- Return code: 0

stdout tail:

```text

```

stderr tail:

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.006s

OK

```

### live_claude_workspace_e2e

- Status: SKIP
- Return code: None

stdout tail:

```text
Skipped by default. Re-run with --live-claude after user confirmation.
```

stderr tail:

```text

```
