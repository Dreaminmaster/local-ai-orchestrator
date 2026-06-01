# Sync Apply Report

Checked on: 2026-06-02

Formal sync directory:

```text
/Users/johnwick/Documents/codex/_beta_sync/local-ai-orchestrator
```

Source successful directory:

```text
/Users/johnwick/Documents/codex/local-ai-orchestrator-main
```

Remote repository:

```text
https://github.com/Dreaminmaster/local-ai-orchestrator
branch: main
```

Base commit used for sync:

```text
e2e4a89e876ffbdd66349fc52e17c9a5cba829b7
```

Note: direct GitHub clone timed out twice, so `_beta_sync` was seeded from the
previous local `_remote_compare/local-ai-orchestrator` clone at the same commit,
then `origin` was set to the official GitHub URL.

## Synced Files

Directly synced from the local successful directory:

- `backend/local_model/external_ai_escalation.py`
- `backend/skills/external_ai_web/answer_extractor.py`
- `backend/skills/external_ai_web/answer_quality_check.py`
- `backend/skills/external_ai_web/claude_web_adapter.py`
- `backend/skills/external_ai_web/evidence_writer.py`
- `backend/skills/external_ai_web/web_ai_skill.py`
- `scripts/e2e_agent_uses_claude_web.py`
- `scripts/e2e_web_ai_retry_main_providers.py`
- `tests/test_claude_answer_extractor_from_evidence.py`
- `frontend/app.js`
- `docs/web_ai_test_matrix.md`
- `BETA_KERNEL_VALIDATION.md`

Added from the local successful directory:

- `backend/evidence/__init__.py`
- `backend/evidence/board.py`
- `backend/evidence/snapshot.py`
- `tests/fixtures/broken_node_syntax/index.js`
- `tests/fixtures/broken_python_syntax/main.py`

Additional dependency files synced to keep the copied Beta kernel code
internally consistent:

- `backend/skills/external_ai_web/base_web_ai_adapter.py`
- `backend/skills/external_ai_web/prompt_sender.py`
- `backend/skills/external_ai_web/chatgpt_web_adapter.py`
- `backend/core/failure_taxonomy.py`
- `backend/core/reporter.py`
- `backend/api/web_ai_profiles.py`
- `frontend/style.css`
- `scripts/test_web_ai_chatgpt.py`
- `scripts/test_web_ai_claude.py`
- `scripts/doctor.py`

## Merged Files

Manually merged:

- `backend/skills/external_ai_web/selectors.py`

Merge details:

- Preserved local robust selectors:
  - `div.ProseMirror`
  - `[role='textbox']`
  - wider Claude message selectors
  - Chinese send-button aria label for ChatGPT
- Preserved remote useful additions:
  - `body_marker`
  - `claude_web` provider alias

## Explicitly Not Synced

The following were not synced into Git:

- `venv/`
- `.playwright-browsers/`
- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `runtime/pip_cache/`
- `runtime/tmp/`
- `.env`
- `backend/storage/orchestrator.db`
- `LOCAL_INSTALL_AUDIT.md`

`LOCAL_INSTALL_AUDIT.md` contains local absolute paths and should not be pushed
unless sanitized.

## Non-Live Check Results

The clean sync directory has no local `venv/`, so the local successful
directory's venv was used while `PYTHONPATH` pointed to the sync directory.

| Check | Result |
|---|---:|
| `venv/bin/python scripts/health_check.py` | PASS |
| `PYTHONPATH=. venv/bin/python scripts/e2e_agent_driven_repair_matrix.py` | PASS |
| `node --check frontend/app.js` | PASS |
| `venv/bin/python -m unittest tests/test_claude_answer_extractor_from_evidence.py` | PASS |

Repair matrix result:

- Report: `runtime/test_reports/e2e_repair_matrix.json`
- Created at: `2026-06-02T03:40:15.722618`
- Passed fixtures: `10/10`

## Live Claude Web E2E Result

After the clean-clone precondition fix, one forced Claude Web live E2E run was
performed.

Command:

```bash
PYTHONPATH=. venv/bin/python scripts/e2e_agent_uses_claude_web.py --force-provider "Claude Web"
```

Because the clean clone had no logged-in browser profile, a local symlink was
created for testing only:

```text
runtime/browser_profiles/claude -> /Users/johnwick/Documents/codex/local-ai-orchestrator-main/runtime/browser_profiles/claude
```

Result:

- `final_status`: PASS
- `selected_target`: Claude Web
- `force_provider`: true
- `requested_provider`: Claude Web
- `provider_status_source`: forced_cli_argument
- `answer_quality`: PASS
- `quality_issues`: none
- `evidence_saved`: true
- `report_contains_claude_web`: true
- Report path: `runtime/test_reports/e2e_agent_uses_claude_web.json`
- Evidence path: `runtime/evidence/web_ai/claude/20260602_035344`

Previous failure classification:

- The first clean-clone live run selected ChatGPT because the clean clone lacked
  `runtime/test_reports/web_ai/claude.json`.
- The synced local router expects provider status reports under
  `runtime/test_reports/web_ai/`.
- The clean clone intentionally did not sync `runtime/`, so it had no Claude PASS
  provider report.
- The E2E script now supports `--force-provider "Claude Web"` so a clean clone
  can explicitly test Claude Web without depending on runtime provider reports.
- The forced rerun passed.

## Git Status Notes

Source files are modified in `_beta_sync` and are ready to commit/push after
final git staging review.

Important: these source/test files are ignored by the current `.gitignore` and
will require `git add -f` if they are committed later:

- `backend/evidence/__init__.py`
- `backend/evidence/board.py`
- `backend/evidence/snapshot.py`
- `tests/fixtures/broken_node_syntax/index.js`
- `tests/fixtures/broken_python_syntax/main.py`

Ignored local runtime files were generated during checks and must remain
untracked:

- `runtime/`

## Beta Clean Version Conclusion

Current result:

- Non-live checks: PASS
- Live Claude Web E2E: PASS
- Commit/push: ready after staging

Therefore this sync directory can be committed as the Beta clean version, while
keeping runtime/profile/cache artifacts out of Git.

Commit message:

```text
Sync local Beta kernel success fixes with forced Claude Web E2E
```
