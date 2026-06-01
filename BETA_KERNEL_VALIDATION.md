# Beta Kernel Validation

Checked on: 2026-06-02

Project root:

```text
/Users/johnwick/Documents/codex/local-ai-orchestrator-main
```

This document summarizes the local portable-mode Beta kernel validation. It is a
local handoff note and intentionally records local paths and runtime evidence
paths.

## 1. Current Portable Deployment Status

Portable runtime locations:

- `venv`: `/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv`
- Playwright browsers: `/Users/johnwick/Documents/codex/local-ai-orchestrator-main/.playwright-browsers`
- Runtime directory: `/Users/johnwick/Documents/codex/local-ai-orchestrator-main/runtime`

Backend status:

- URL checked: `http://localhost:8422`
- Result: reachable
- HTTP status: `200 OK`
- Server observed: `uvicorn`

Repair matrix:

- Script: `scripts/e2e_agent_driven_repair_matrix.py`
- Latest report: `runtime/test_reports/e2e_repair_matrix.json`
- Latest created_at: `2026-06-02T02:45:00.698321`
- Result: PASS
- Passed fixtures: `10/10`

Portable constraints followed during validation:

- No global dependency installation.
- No `brew install`.
- No system environment modification.
- No Python, Git, LM Studio, or Ollama installation.
- Playwright Chromium used from project-local `.playwright-browsers/`.
- Python dependencies used from project-local `venv/`.
- Web AI profiles used from project-local `runtime/browser_profiles/`.

## 2. Web AI Provider Status

Main providers tested:

| Provider | Status | Evidence Path | Notes |
|---|---:|---|---|
| Claude Web | PASS | `runtime/evidence/web_ai/claude/20260601_232239` | Main preferred external AI provider. |
| ChatGPT Web | PARTIAL | `runtime/evidence/web_ai/chatgpt/20260601_232216` | Available as fallback but unstable; prior extraction used `body_fallback`. |

Provider matrix:

```text
docs/web_ai_test_matrix.md
```

Main provider retry report:

```text
runtime/test_reports/web_ai/main_providers_retry.json
```

## 3. Claude Web Practical Agent E2E

Scenario:

```text
scripts/e2e_agent_uses_claude_web.py
```

Final result:

- `final_status`: PASS
- `selected target`: Claude Web
- `used_selector`: `body_marker:claude`
- `answer_quality`: PASS
- `quality_issues`: none
- `evidence_saved`: true
- `report_contains_claude_web`: true
- Report path: `runtime/test_reports/e2e_agent_uses_claude_web.json`
- Evidence path: `runtime/evidence/web_ai/claude/20260602_025237`

Observed successful chain:

- Failure taxonomy returned `external_ai_needed`.
- `ExternalAIEscalationRouter` selected `Claude Web`.
- `WebAISkill` used the project-local Claude profile:
  `runtime/browser_profiles/claude/`.
- Prompt was redacted before external submission.
- Claude Web returned a usable answer.
- Evidence was saved.
- Reporter output included `使用 Claude Web 外部求助`.

## 4. Current Local Modified Files

This folder is not currently a git repository, so `git status` cannot provide an
authoritative diff. The following list is based on the files created or modified
during the local Beta validation session.

Backend code:

- `backend/api/web_ai_profiles.py`
- `backend/core/failure_taxonomy.py`
- `backend/core/reporter.py`
- `backend/evidence/__init__.py`
- `backend/evidence/board.py`
- `backend/evidence/snapshot.py`
- `backend/local_model/external_ai_escalation.py`
- `backend/skills/external_ai_web/answer_extractor.py`
- `backend/skills/external_ai_web/answer_quality_check.py`
- `backend/skills/external_ai_web/base_web_ai_adapter.py`
- `backend/skills/external_ai_web/claude_web_adapter.py`
- `backend/skills/external_ai_web/evidence_writer.py`
- `backend/skills/external_ai_web/prompt_sender.py`
- `backend/skills/external_ai_web/web_ai_skill.py`

Scripts:

- `scripts/doctor.py`
- `scripts/e2e_agent_uses_claude_web.py`
- `scripts/e2e_web_ai_retry_main_providers.py`
- `scripts/test_web_ai_chatgpt.py`
- `scripts/test_web_ai_claude.py`

Tests and fixtures:

- `tests/test_claude_answer_extractor_from_evidence.py`
- `tests/fixtures/broken_python_syntax/main.py`
- `tests/fixtures/broken_node_syntax/index.js`

Docs:

- `docs/web_ai_test_matrix.md`
- `BETA_KERNEL_VALIDATION.md`

Frontend:

- `frontend/app.js`
- `frontend/style.css`

Local audit:

- `LOCAL_INSTALL_AUDIT.md`
- Contains local machine paths such as:
  `/Users/johnwick/Documents/codex/local-ai-orchestrator-main`
- Recommendation: do not push this file directly to a public GitHub repository
  unless it is sanitized or intentionally kept as a local-only audit artifact.

Runtime reports generated locally:

- `runtime/test_reports/e2e_agent_uses_claude_web.json`
- `runtime/test_reports/e2e_repair_matrix.json`
- `runtime/test_reports/web_ai/main_providers_retry.json`
- `runtime/evidence/web_ai/...`

These are validation artifacts, not source code.

## 5. Files That Should Be Pushed To GitHub

Recommended source changes to sync into the formal repository:

- `backend/api/web_ai_profiles.py`
- `backend/core/failure_taxonomy.py`
- `backend/core/reporter.py`
- `backend/evidence/__init__.py`
- `backend/evidence/board.py`
- `backend/evidence/snapshot.py`
- `backend/local_model/external_ai_escalation.py`
- `backend/skills/external_ai_web/answer_extractor.py`
- `backend/skills/external_ai_web/answer_quality_check.py`
- `backend/skills/external_ai_web/base_web_ai_adapter.py`
- `backend/skills/external_ai_web/claude_web_adapter.py`
- `backend/skills/external_ai_web/evidence_writer.py`
- `backend/skills/external_ai_web/prompt_sender.py`
- `backend/skills/external_ai_web/web_ai_skill.py`
- `scripts/doctor.py`
- `scripts/e2e_agent_uses_claude_web.py`
- `scripts/e2e_web_ai_retry_main_providers.py`
- `scripts/test_web_ai_chatgpt.py`
- `scripts/test_web_ai_claude.py`
- `tests/test_claude_answer_extractor_from_evidence.py`
- `tests/fixtures/broken_python_syntax/main.py`
- `tests/fixtures/broken_node_syntax/index.js`
- `frontend/app.js`
- `frontend/style.css`

Docs that may be pushed after review:

- `docs/web_ai_test_matrix.md`
- `BETA_KERNEL_VALIDATION.md`

If pushing docs publicly, consider replacing local absolute paths with relative
paths or a sanitized example path.

## 6. Files That Should Not Be Pushed

Do not push local runtime, dependency, browser, or profile artifacts:

- `venv/`
- `.playwright-browsers/`
- `runtime/`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `runtime/pip_cache/`
- `runtime/tmp/`
- `.env`
- Any local browser profile, cookies, login state, screenshots, or evidence
  containing account/session/page data.

Do not directly push local-only audit files if they expose machine-specific
paths or environment details:

- `LOCAL_INSTALL_AUDIT.md`

`LOCAL_INSTALL_AUDIT.md` can be converted into a sanitized template before
publication if the official repo needs install-audit documentation.

## 7. Next Step Recommendations

Recommended sequence:

1. Sync the local source fixes into the formal GitHub repository.
2. Have the remote assistant or repository maintainer review this local
   validation result and prepare a clean commit.
3. Suggested commit scope:
   `Use Claude Web as preferred escalation provider`.
4. Keep local runtime artifacts out of the commit.
5. Recreate formal validation reports in the repository or CI using sanitized
   evidence paths where possible.
6. After the Beta kernel is stable, continue with the planned External AI
   Workspace persistent work area.

Suggested commit contents:

- Claude Web preferred provider routing.
- ChatGPT PARTIAL fallback handling.
- Claude answer extraction reliability improvements.
- Web AI evidence persistence improvements.
- Claude Web Agent E2E script and offline regression test.
- Web UI provider state labels.

Suggested non-commit local artifacts:

- `runtime/`
- `venv/`
- `.playwright-browsers/`
- `.env`
- `LOCAL_INSTALL_AUDIT.md` unless sanitized.
