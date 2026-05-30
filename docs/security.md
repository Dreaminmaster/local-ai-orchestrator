# Security and Permission Model

## Risk Levels

| Level | Examples | Policy |
|---|---|---|
| low | read files, screenshots, search | auto allowed |
| medium | run commands, modify files, install packages | allowed in auto mode, logged |
| high | delete files, send messages, git push, upload private files | requires confirmation |
| critical | payment, trading, credential changes, system destruction | blocked or explicit confirmation only |

## Principles

1. High-risk actions are never fully automatic.
2. All actions must be logged.
3. File modifications should create snapshots.
4. External data upload must be explicit.
5. Unknown code should run in sandbox when possible.

## Implemented

- `backend/security/permissions.py`
- risk assessment for shell commands and file operations
- destructive pattern blocking
- snapshot manager for rollback

## Planned

- UI confirmation queue
- per-project sandbox directory
- allowlist / denylist policies
- credential redaction in logs
