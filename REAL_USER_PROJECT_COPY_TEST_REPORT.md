# Real User Project Copy Test Report

## Copy Locations

Both source projects were copied into the existing archive root. Original projects
were not modified.

- Python: `test-workspaces/final-product-usability/money-agent-copy`
- Next/React: `test-workspaces/final-product-usability/get-more-copy`

## Results

### money-agent

- Structure scan: PASS
- Goal Contract and plan: PASS
- `python3 -m compileall -q app`: PASS
- Task history, checkpoint, resume, report: PASS
- Reliable source changes required: none

### get-more

- Structure scan: PASS
- Goal Contract and plan: PASS
- `npm run build`: PASS
- Rollback and reverify: PASS
- Claude diagnostic joint task: PASS
- Reliable source changes required: none

No artificial defects were injected. The only discovered failure was caused by
the orchestrator checkpoint implementation dereferencing project symlinks; that
orchestrator bug was fixed and validated.
