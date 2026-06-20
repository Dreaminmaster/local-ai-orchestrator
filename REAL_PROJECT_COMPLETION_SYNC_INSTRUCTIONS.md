# Real Project Completion Sync Instructions

Apply `real_project_completion_sprint.patch` to the matching workspace-alpha
baseline, review the scoped files, then run:

```bash
PYTHONPATH=. .build-venv/bin/python scripts/e2e_real_project_completion_matrix.py
PYTHONPATH=. .build-venv/bin/python scripts/e2e_agent_driven_repair_matrix.py
.build-venv/bin/python scripts/health_check.py
PYTHONPATH=. .build-venv/bin/python scripts/beta_validation.py
node --check frontend/app.js
```

Do not run live Claude or another provider for this validation. Do not commit
`runtime/`, isolated test projects, profiles, evidence, dependency directories,
target output, app bundles, binaries, or environment files.
