# Final Installed App Acceptance Report

Generated: 2026-06-21 16:12 Asia/Shanghai

## Overall Result

Final installed App acceptance: PARTIAL

Installation, startup, architecture, LM Studio, Provider Console, supported repair flows, resume/rollback, and shutdown cleanup passed.

The result is PARTIAL because two broader expectations are not fully satisfied:

- Generic arbitrary repair prompts such as a plain `print(message)` project did not auto-repair through the installed real-project runner. The supported marker-based repair fixtures do pass.
- Reopening Claude workspace did not create a second context, but the second open returned a new request id and did not mark `workspace_reused=true`; this is safe but not a perfect duplicate-click/reuse signal.

## Installed Main App

- Installed App path: `/Applications/Local AI Orchestrator.app`
- Source DMG: `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-provider-console-unsigned.dmg`
- Expected SHA-256: `a3da1f80e76d7efaf4e16d69b712529c77c2d56a96273cec7e3b9a80c4ad50a8`
- Actual SHA-256: `a3da1f80e76d7efaf4e16d69b712529c77c2d56a96273cec7e3b9a80c4ad50a8`
- SHA match: PASS

Old `/Applications` App backup:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/old-apps/Local AI Orchestrator-20260621_160330.app`

## Launch And Health

- App launch via macOS `open`: PASS
- App window appeared: PASS, verified with Computer Use
- `/api/health`: PASS
- `/api/ui-ready`: PASS
- Desktop shell mode: `packaged / tauri`
- App data root: `/Users/johnwick/Library/Application Support/com.dreaminmaster.local-ai-orchestrator`
- Project browser status: installed

## Architecture

Installed `/Applications` App architecture audit:

- Result: PASS
- Mach-O files scanned: `84`
- x86_64-only files: `0`
- Main Tauri executable: arm64
- Bundled backend sidecar: arm64

No shell-detectable Intel component warning root cause remains.

## LM Studio

- `http://127.0.0.1:1234/v1/models`: PASS, HTTP 200
- Minimal chat completion: PASS, model returned `OK`
- App health state: LM Studio `READY`
- Acceptance status: `VERIFIED`
- Default model: `qwen2.5-coder-14b-instruct-mlx`
- Roles exposed by health: planner, executor, repair, verifier, summarizer
- Ollama: disabled by user choice

## Local Task Acceptance

Installed sidecar was used for these checks; development backend was not used.

### File Create / Read

- Contract task created `hello.txt`: PASS
- `hello.txt` content: `Local AI Orchestrator smoke test`
- Agent event report generated in task events: PASS
- `report.md` inside the isolated project directory: PARTIAL, not created by this deterministic compiler path

### Shell Task

- Shell capability was exercised through real-project verification commands: PASS
- Direct contract shell task returned `completed_unverified` and did not write project-local `report.md`: PARTIAL

### Supported Python NameError Repair

- Fixture: `UNDEFINED_MESSAGE`
- Result: PASS
- Task id: `real-9a170af6d2`
- Modified file: `main.py`
- Verification: `python3 -m unittest discover -s tests -v`
- External AI calls: `0`

### Supported ImportError Repair

- Fixture: `MISSING_IMPORT`
- Result: PASS
- Task id: `real-f93e75ee7e`
- Modified file: `app/core.py`
- Verification: `python3 -m unittest discover -s tests -v`
- External AI calls: `0`

### Generic Runtime Entry Verification

Plain broken projects such as `print(message)` or `import nonexistent_final_acceptance_module` were correctly not misclassified as success:

- `compileall` may pass, but `python3 main.py` failure returns `verification_failed`.
- This confirms the runtime-entry verification fix remains active.
- It also means generic arbitrary repair remains outside the current supported repair fixture scope.

### Small Project Scan / Repair / Verify / Report

- Project: Python CLI with `MISSING_IMPORT`, `LOGIC_BUG`, and `UNDEFINED_MESSAGE`
- Result: PASS
- Task id: `real-141a38bbda`
- Modified files: `app/cli.py`, `app/core.py`
- Final report: PASS
- External AI calls: `0`

## Task History, Realtime Events, Resume, Rollback

- Task history list: PASS
- Realtime events persisted: PASS
- Final report retrieval: PASS
- Supported interrupted task: `INTERRUPTED`
- Resume: PASS
- Rollback: PASS
- Rollback restored the isolated project to checkpoint state

## Provider Console

UI and API verified:

- AI 服务 page exists: PASS
- 设置与诊断 page exists: PASS
- Provider Workspace Console exists: PASS
- Claude / ChatGPT / Gemini / Kimi / 豆包 rows exist: PASS
- Each row exposes workspace status and project-specific App Data profile path: PASS
- Unverified web providers are not route eligible: PASS
- Routing decision selects LM Studio, not unverified web providers: PASS

Workspace open guard:

- Claude workspace opened with project-specific App Data profile: PASS
- `second_context_created=false`: PASS
- Second open did not mark `workspace_reused=true` and generated a new request id: PARTIAL
- Workspace was closed after the check: PASS

No live web provider prompts were sent in this final installed acceptance run.

## Routing

Routing decision checks:

- `allow_external=false`: selected `lmstudio`
- `allow_external=true`, user not confirmed: selected `lmstudio`
- `allow_external=true`, user confirmed: selected `lmstudio`

Unverified web providers were safely excluded from automatic routing.

## Exit And Cleanup

- App normal quit: PASS
- App-owned sidecar shutdown: PASS
- Port 8422 residue: none
- Port 8423 residue: none
- DMG unmounted: PASS
- Old `/Applications` App moved to `old-apps/`: PASS
- Older test workspaces moved to `test-workspaces/old/`: PASS
- Current main DMG retained: PASS
- Final patch / backup / reports retained: PASS

## Evidence Files

Staging evidence:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/staging/final-installed-app-acceptance/`

Current test workspaces:

- `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/test-workspaces/final-installed-app-acceptance`
- `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/test-workspaces/final-installed-app-acceptance-supported`
- `/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/test-workspaces/final-installed-app-acceptance-small-project`

## Manual Follow-Up Needed

No manual action is needed to use the installed App locally with LM Studio.

Optional later actions:

- Log in to Claude / ChatGPT / Gemini / Kimi / Doubao inside AI 服务 if you want web-provider routing.
- Generic arbitrary repair path has now been expanded in source: plain `print(message)` and safe local import mismatch cases pass the new generic repair matrix.
- Workspace repeated-open semantics have now been tightened in source: second open reports stable `workspace_id`, `workspace_reused=true`, `same_window_focused=true`, and `second_context_created=false`.
- These source fixes have not yet been rebuilt into a replacement DMG.

## Source Follow-Up - 2026-06-21

- Generic repair matrix: PASS, 10/10 expected outcomes.
- Workspace reuse semantics tests: PASS.
- Provider Console API smoke: PASS.
- Live provider prompts during this follow-up: 0.

## v0.3.2 Isolated DMG Smoke - 2026-06-21

- v0.3.2 unsigned DMG generated and mounted.
- Isolated App launch: PASS.
- `/api/health`: PASS.
- `/api/ui-ready`: PASS.
- Packaged generic repair smoke: PASS.
- Packaged workspace reuse smoke: PASS.
- Product core smoke: PASS.
- 8422/8423 cleanup: PASS.
- Current `/Applications` main App was not replaced.
