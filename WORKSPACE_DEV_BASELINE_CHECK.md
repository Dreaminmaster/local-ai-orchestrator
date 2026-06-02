# Workspace Dev Baseline Check

Generated: 2026-06-02T12:05:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

## Baseline Source

- Current workspace HEAD: `d42701a`
- This workspace was seeded from the local verified Beta kernel commit, not from a fresh GitHub tag checkout.
- No live Claude Web run was executed in this baseline check.
- No runtime, browser profile, `.playwright-browsers`, `.env`, or venv data was copied into this workspace.

## v0.1.1 Key Fix Audit

Status: **PASS after baseline补齐**

### Forced Claude Web E2E

`scripts/e2e_agent_uses_claude_web.py` contains:

- `--force-provider`
- `provider_status_source`
- `requested_provider`
- `skipped_reason`
- `answer_quality`

Result: **PASS**

### Answer Quality Captcha Rules

`backend/skills/external_ai_web/answer_quality_check.py` now uses precise captcha phrases:

- `captcha`
- `verify you are human`
- `human verification`
- `验证码`
- `人机验证`
- `安全验证`
- `请验证你是真人`

Removed broad or risky matches:

- `security challenge`
- `prove you are human`
- `请验证你是人类`

No standalone broad rules were found for:

- `verify`
- `challenge`
- `人类`
- `验证`

Result: **PASS**

### Escalation Router

`backend/local_model/external_ai_escalation.py` now:

- Reads provider reports from `runtime/test_reports/web_ai/*.json`.
- Sorts provider status by `PASS > PARTIAL > FAIL > NOT_RUN`.
- Automatically selects only `PASS` or `PARTIAL` Web providers.
- Keeps `FAIL` and untested providers out of automatic Web provider selection.
- Includes `external_ai_needed`.
- Weights Claude Web ahead of ChatGPT Web for `code_repair_failed`, `external_ai_needed`, and `planner_uncertain`.

Result: **PASS**

## Productization Features Added In Workspace Dev

- Beta validation entry:
  - `scripts/beta_validation.py`
  - `8_运行Beta验收.command`
  - `8_运行Beta验收.bat`
  - `BETA_VALIDATION_REPORT.md`
- Web AI provider matrix backend API:
  - `GET /api/web-ai/test-matrix`
  - matrix detail fields for failure reason, selector, quality issues, evidence, screenshot, and metadata paths.
- Web AI provider matrix frontend panel:
  - Provider, Login, Send, Wait, Extract, AQ, Status, Last Tested, Evidence.
  - Clickable provider detail panel.
- External AI Workspace manager:
  - `backend/skills/external_ai_web/workspace_manager.py`
  - `open_workspace(provider)`
  - `ensure_workspace(provider)`
  - `reuse_existing_page(provider)`
  - `close_workspace(provider)`
  - `get_workspace_status(provider)`
- Unified provider status helpers:
  - `backend/skills/external_ai_web/provider_status.py`
  - `NOT_CONFIGURED`
  - `NEED_LOGIN`
  - `READY`
  - `PASS`
  - `PARTIAL`
  - `FAIL`
  - `NEED_USER_INTERVENTION`
- WebAISkill can reuse an existing project-local workspace page when available.
- Claude Workspace stale conversation recovery:
  - Detects `This conversation could not be found`, `Conversation not found`, `chat not found`, `unavailable`, and `not found`.
  - Marks those pages as `STALE_CONVERSATION`.
  - Recovers Claude Web by navigating the existing page to `https://claude.ai/new`.
  - Does not reset profile, does not close the browser context, and does not fall back to ChatGPT.
  - WebAISkill calls `ensure_workspace(provider)` before sending a prompt.
  - Recovery metadata is recorded for the next live E2E report.

## Non-Live Check Results

The first plain `python3` attempt failed because this clean workspace does not have its own `venv/` and dependencies such as `httpx` are not installed locally. No dependencies were installed during this check.

The checks below borrowed:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python`

with `PYTHONPATH` pointing to:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

| Check | Result |
|---|---:|
| `scripts/health_check.py` | PASS |
| `scripts/e2e_agent_driven_repair_matrix.py` | PASS, 10/10 |
| `node --check frontend/app.js` | PASS |
| `python -m unittest tests/test_claude_answer_extractor_from_evidence.py` | PASS, 3 tests |
| `python -m unittest tests/test_workspace_recovery.py` | PASS, 5 tests |
| `scripts/beta_validation.py` | PASS, live Claude skipped |

Latest repair matrix timestamp:

`2026-06-02T12:19:01.163411`

Beta validation report:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/BETA_VALIDATION_REPORT.md`

## Claude Workspace Live Test Readiness

Status: **READY FOR USER-CONFIRMED SINGLE LIVE RERUN**

The workspace-dev code baseline is ready for Claude Workspace live testing, but the first live attempt was invalidated because the user confirmed they had not finished logging in.

Latest workspace live report:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime/test_reports/e2e_claude_workspace_live.json`

Previous invalidated live status:

- `final_status`: `SKIP`
- `need_user_intervention`: `true`
- `failure_reason`: `claude_profile_missing_or_not_logged_in_user_confirmed`
- `live_result_trusted`: `false`

After manual login confirmation, one Claude Workspace live E2E was run:

- report: `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime/test_reports/e2e_claude_workspace_live.json`
- `final_status`: `FAIL`
- `provider`: `Claude Web`
- `selected_target`: `Claude Web`
- `workspace_opened`: `true`
- `reused_existing_page`: `true`
- `answer_quality`: `PARTIAL`
- `quality_issues`: `body_fallback`
- `evidence_saved`: `true`
- `evidence_path`: `runtime/evidence/web_ai/claude/20260602_121124`
- `report_contains_claude_web`: `true`
- `need_user_intervention`: `false`
- `failure_reason`: `Answer quality check failed: body_fallback`
- `used_selector`: `body_fallback`

Failure classification:

- Workspace reuse: PASS
- Provider selection: PASS
- Evidence save: PASS
- Reporter Claude Web mention: PASS
- Claude page state: FAIL, page showed `This conversation could not be found. Conversation not found.`
- Answer extraction: FAIL/PARTIAL, no reliable assistant selector was found and extraction fell back to body text.
- Answer quality check: Correctly downgraded to PARTIAL because `body_fallback` is not reliable.

Stale conversation recovery has now been implemented and covered by offline tests. Do not rerun live repeatedly; the next live E2E should be run only once after user confirmation.

## Network Error Offline Analysis

Evidence inspected:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime/evidence/web_ai/claude/20260602_123322`

Classification: **B. Claude normal answer contained technical network/connection/timeout words and triggered an overly broad quality rule.**

Findings:

- `answer.txt` contains a normal Claude assistant answer.
- `metadata.json` shows `used_selector=[class*='font-claude']`.
- `body_fallback=false`.
- `candidate_selectors.json` shows the assistant answer candidate was chosen.
- `screenshot.png` shows a normal Claude conversation answer, not a network error page.
- There was no `answer_raw_body_fallback.txt`.

Fixes applied:

- `answer_quality_check.py` now only flags explicit network error phrases such as `network error`, `connection lost`, `connection failed`, `unable to connect`, `request timed out`, `reconnecting`, `网络错误`, `无法连接`, `连接失败`, and `请求超时`.
- Generic terms such as `network`, `connection`, and `timeout` no longer trigger `network_error` by themselves.
- `answer_extractor.py` rejects page error banners as `page_error_banner` instead of treating them as assistant answers.
- `workspace_manager.py` can classify real page network errors as `PAGE_NETWORK_ERROR`.
- `WebAISkill` treats page network error states as requiring intervention instead of falling back to another provider.

Additional offline tests:

- `tests/test_answer_quality_check.py`: PASS, 2 tests.
- `tests/test_claude_answer_extractor_from_evidence.py`: PASS, 4 tests.
- `tests/test_workspace_recovery.py`: PASS, 6 tests.

Latest non-live validation:

- `scripts/health_check.py`: PASS.
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10.
- `node --check frontend/app.js`: PASS.
- `scripts/beta_validation.py`: PASS, live Claude skipped.

## Login Required Offline Analysis

Evidence inspected:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/runtime/evidence/web_ai/claude/20260602_142531`

Classification: **C. Claude adapter login detection was too strict and disagreed with WorkspaceManager.**

Findings:

- `metadata.json` shows `send_success=false` and `extract_success=false`.
- `candidate_selectors.json` is empty, so no extraction happened.
- `answer.txt` is empty.
- `screenshot.png` shows a usable Claude composer page with `Good afternoon, Genius One` and a visible prompt composer.
- WorkspaceManager reported `READY` before send.
- Claude adapter then returned `Login required` because its old login detector did not use the same READY logic.

Fixes applied:

- Claude adapter now uses WorkspaceManager's unified page state detection for login readiness.
- Claude composer wait selector includes `[role='textbox']`.
- Workspace READY is stricter:
  - not login/auth URL,
  - no `sign in`, `log in`, `continue with google`,
  - no `session expired` / `please log in again`,
  - no stale conversation,
  - no page network error,
  - no captcha / human verification,
  - composer/input visible.
- WebAISkill no longer treats login/provider readiness as answer quality failure.
- Login/provider readiness failures return `need_user_intervention=true` and `failure_reason=claude_login_required`.
- `Login required` no longer appears as an answer quality issue.

Additional offline tests:

- `tests/test_workspace_login_state.py`: PASS, 6 tests.

Latest non-live validation after login-state fix:

- `scripts/health_check.py`: PASS.
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10.
- `node --check frontend/app.js`: PASS.
- `tests/test_claude_answer_extractor_from_evidence.py`: PASS, 4 tests.
- `tests/test_workspace_recovery.py`: PASS, 6 tests.
- `tests/test_answer_quality_check.py`: PASS, 2 tests.
- `tests/test_workspace_login_state.py`: PASS, 6 tests.
- `scripts/beta_validation.py`: PASS, live Claude skipped.

## v0.2 Workspace Product Loop

Decision:

- Stop chasing Claude Workspace live E2E absolute PASS.
- Treat login, verification, stale page, and provider page instability as normal product states.
- Product behavior is now detect, pause, explain, preserve state, and resume after user action.

New live E2E final statuses:

- `PASS`: automatic Claude Workspace flow completed.
- `NEED_USER_INTERVENTION`: system correctly paused for login, verification, stale page, or recoverable provider page state.
- `FAIL`: program error or unrecoverable failure.

Workspace intervention fields:

- `need_user_intervention`
- `intervention_reason`
- `suggested_user_action`
- `can_resume_after_user_action`
- `workspace_status_before_send`
- `failure_reason`

WebAISkill intervention metadata:

- `need_user_intervention=true`
- `provider_status`
- `failure_reason`
- `suggested_user_action`
- `can_resume=true`

Frontend workspace actions:

- Open workspace.
- Recheck status.
- Test provider workspace.
- I handled it, continue.
- Reset profile.
- View evidence.

Frontend status copy:

- `READY`: 可用
- `PASS`: 已测试通过
- `PARTIAL`: 可用但不稳定
- `NEED_LOGIN`: 需要登录
- `NEED_USER_INTERVENTION`: 需要你处理
- `FAIL`: 测试失败
- `NOT_CONFIGURED`: 未配置

Beta validation semantics:

- `core_pass`
- `workspace_auto_pass`
- `workspace_needs_user`
- `blocking_failures`
- Workspace needing user login/verification is a resumable state, not a beta kernel failure.

Latest non-live validation after v0.2 product-loop change:

- `scripts/health_check.py`: PASS.
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10.
- `node --check frontend/app.js`: PASS.
- `tests/test_claude_answer_extractor_from_evidence.py`: PASS, 4 tests.
- `tests/test_workspace_recovery.py`: PASS, 6 tests.
- `tests/test_answer_quality_check.py`: PASS, 2 tests.
- `tests/test_workspace_login_state.py`: PASS, 6 tests.
- `tests/test_beta_validation_status.py`: PASS, 1 test.
- `scripts/beta_validation.py`: PASS, live Claude skipped.

## Product Shell Pending External AI Resume

Implemented:

- Pending External AI actions are saved to `runtime/tasks/{task_id}/pending_external_ai.json`.
- Pending payload includes task id, step id, provider, original prompt, redacted prompt, context, provider status, failure reason, suggested user action, `can_resume`, and creation time.
- `GET /api/external-ai/pending` lists pending actions.
- `POST /api/external-ai/{task_id}/resume` rechecks provider status before sending.
- If provider still needs login or intervention, resume returns `still_needs_user=true` and does not send.
- If provider is READY/PASS/PARTIAL, resume re-executes the pending WebAISkill action, saves evidence/result, and returns a resume payload for continuing the task.
- Agent event stream now emits:
  - `external_ai_need_user`
  - `external_ai_pending_saved`
  - `external_ai_resume_started`
  - `external_ai_resume_success`
  - `external_ai_resume_still_needs_user`
  - `external_ai_resume_failed`
- Frontend task pause panel can show pending External AI action and resume it after user handling.

Latest non-live validation after pending/resume product shell:

- `scripts/health_check.py`: PASS.
- `scripts/e2e_agent_driven_repair_matrix.py`: PASS, 10/10.
- `node --check frontend/app.js`: PASS.
- `tests/test_pending_external_ai_resume.py`: PASS, 3 tests.
- `tests/test_workspace_login_state.py`: PASS, 6 tests.
- `tests/test_beta_validation_status.py`: PASS, 1 test.
- `tests/test_workspace_recovery.py`: PASS, 6 tests.
- `tests/test_answer_quality_check.py`: PASS, 2 tests.
- `tests/test_claude_answer_extractor_from_evidence.py`: PASS, 4 tests.
- `scripts/beta_validation.py`: PASS, live Claude skipped.

Expected live command after confirmation:

```bash
PYTHONPATH=. python3 scripts/e2e_claude_workspace_live.py
```

For portable mode, use only project-local profiles:

- `runtime/browser_profiles/claude/`
- `runtime/browser_profiles/chatgpt/`
- `runtime/browser_profiles/doubao/`
- `runtime/browser_profiles/kimi/`
- `runtime/browser_profiles/gemini/`

Do not use daily Chrome or Safari profiles.

## Do Not Commit

Do not commit or push:

- `venv/`
- `runtime/`
- `.playwright-browsers/`
- `.env`
- `runtime/browser_profiles/`
- `runtime/evidence/`
- `runtime/test_reports/`
- `runtime/pip_cache/`
- `runtime/tmp/`
