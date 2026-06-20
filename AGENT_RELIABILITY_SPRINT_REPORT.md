# Agent Reliability Sprint Report

## Result

**Agent Reliability Sprint: PASS**

The local Agent now completes a 10-case offline task matrix without live External AI. Basic file, shell, repair, pending-user, task history, browser UI, and packaged sidecar API flows are all usable within the tested scope.

## Scope And Safety

- No live Claude call was made.
- No ChatGPT, Doubao, Kimi, or Gemini provider was tested.
- No provider profile was reset.
- No Playwright browser was downloaded.
- No release packaging, signing, notarization, updater, or Windows work was performed.
- Generated runtime data, profiles, evidence, binaries, app bundles, and build targets are not intended for source control.

## LM Studio Stability

### Current Call Chain

- Provider: `LMStudioProvider`
- Endpoint: `http://localhost:1234/v1/chat/completions`
- Default model name: `local-model`
- Request shape: OpenAI-compatible `model`, `messages`, `temperature`, `max_tokens`, and optional JSON response mode
- Previous timeout: 120 seconds per HTTP request
- Previous behavior: HTTP 502 or invalid JSON could delay planning, verification, failure diagnosis, and reporting

### 502 Classification

The earlier HTTP 502 was an upstream local-model service error, not a File or Shell tool failure. During this sprint:

- `GET /v1/models`: HTTP 200
- Minimal `POST /v1/chat/completions`: HTTP 200
- LM Studio returned a loaded model response successfully

The 502 was therefore treated as intermittent local-model availability/error behavior. The Agent no longer depends on successful model completion for recognized basic local tasks.

### Graceful Handling

Local-model retry fallback now returns structured status:

- `LOCAL_MODEL_UNAVAILABLE`
- `LOCAL_MODEL_ERROR`
- `FALLBACK_USED`

The UI displays a clear rule-planning fallback message. Evidence records only a compact error summary such as exception class and HTTP status, not prompts, response bodies, keys, or other sensitive content.

## Rule Fallback Planner

The deterministic planner now supports:

- `create_file`
- `read_file`
- `run_shell`
- `summarize_file`
- `generate_report`
- `repair_python_name_error`
- `repair_python_import_error`
- `repair_python_syntax_error`
- `repair_node_reference_error`
- `repair_package_script`
- `pending_external_ai_mock`

Structured tasks use rule-based failure diagnosis, verification, and report generation. They do not wait for the local model when the local model is unavailable or returns an error.

## Task Matrix

Report: `runtime/test_reports/e2e_agent_task_matrix.json`

| Case | Result |
| --- | --- |
| Create text file and summarize | PASS |
| Read file and write report | PASS |
| Run `python3 --version` and record output | PASS |
| Run a successful Python file | PASS |
| Repair Python NameError | PASS |
| Repair Python ImportError | PASS |
| Repair Python SyntaxError | PASS |
| Repair Node ReferenceError | PASS |
| Repair package script error | PASS |
| Pending External AI mock pause | PASS |

**Task matrix: 10/10 PASS**

The final matrix completed without any live External AI call. Rule-planned cases completed in milliseconds rather than waiting on repeated local-model calls.

## Repair Reliability

The existing Agent-driven repair matrix was also rerun:

**Repair matrix: 10/10 PASS**

It covered Python, Node, missing package, module-not-found, syntax, and package-script repair fixtures.

## Task History Persistence

Each Agent task now has a durable directory under:

`runtime/tasks/{task_id}/`

Artifacts include:

- `task_state.json`
- `plan.json`
- `step_logs.jsonl`
- `final_report.md`
- `step_state.json`, when resumable checkpoint state exists
- `pending_external_ai.json`, when user intervention is required

Task APIs:

- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/report`
- `POST /api/tasks/{task_id}/resume`

The frontend now displays recent tasks, status, failure reason, user-intervention state, and a View Report button.

## UI Task Flow

Browser UI validation passed for:

1. Entering a basic file task
2. Selecting a project path
3. Starting execution
4. Displaying local-model fallback status
5. Displaying a two-step plan
6. Displaying tool calls and step success
7. Displaying evidence count and evidence entries
8. Displaying final verification and final report
9. Displaying the completed task in Recent Tasks
10. Opening the persisted final report

UI task:

`创建 reliability-ui.txt，内容写入 Agent reliability UI smoke，然后读取它并生成总结报告。`

Result: PASS

The Browser console contained no relevant warnings or errors. Screenshot capture timed out, so DOM and interaction state were used as the automated UI proof.

## Packaged App Core Smoke

The current packaged app was rebuilt locally with the latest onedir sidecar and tested through its bundled backend API.

- Packaged sidecar `/api/health`: PASS
- Packaged Product Core API E2E: PASS
- File task: PASS
- Shell task: PASS
- NameError repair task: PASS
- Pending External AI simulation: PASS

A packaged macOS sidecar environment issue was found and fixed: terminal commands did not inherit common macOS executable paths, causing `python3 --version` to time out. `ShellSkill` now supplies a controlled common macOS PATH and structured task failures no longer repeat indefinitely.

Direct automated clicking inside the packaged Tauri WebView remains PARTIAL. The packaged API execution is PASS, while the browser UI interaction flow is PASS.

## Tests

- Agent reliability unit tests: PASS
- Workspace and answer-quality regression tests: PASS
- Task matrix: 10/10 PASS
- Repair matrix: 10/10 PASS
- Repository health check: PASS
- Beta validation: PASS, live Claude skipped
- `node --check frontend/app.js`: PASS
- `git diff --check`: PASS

## Real Capabilities

- Basic local tasks continue when LM Studio is unavailable or returns an error
- Deterministic planning for common file, shell, and repair tasks
- File and Shell tool execution with evidence
- Python and Node repair templates
- Pending External AI pause without a live provider call
- Durable task history and final reports
- Recent-task and report UI
- Packaged sidecar API execution

## Remaining Gaps

- General free-form tasks outside the rule planner still depend on local-model quality.
- The rule repair planner is intentionally conservative and does not cover arbitrary code repair.
- Direct packaged WebView click automation remains incomplete.
- Live External AI workflow was intentionally excluded.
- Task history migration and retention policy need future product design.

## Recommendation

The local core is ready for a controlled External AI live workflow stage, but only after the user explicitly confirms live provider use. The next reliability work should focus on free-form planner quality and broader safe repair templates, not release packaging.

## External AI Workflow Follow-up

The next-stage offline Claude pending/resume workflow passed. A real-user-shaped local project repair smoke also passed. Live Claude remained skipped because the workspace-dev project-specific Playwright Chromium is missing; the application now presents this as `PLAYWRIGHT_BROWSER_MISSING` instead of attempting an unsafe fallback.

## Real Project Completion Follow-up

- Four isolated multi-file project cases passed end to end.
- Goal Contracts, detailed plans, command evidence, diffs, reports, resume, and
  rollback are durable.
- Repair matrix remains 10/10 PASS.
- Packaged backend/API real-project execution passed.
- Actual Claude calls during this follow-up: 0.
- Direct packaged WebView click automation remains PARTIAL.
