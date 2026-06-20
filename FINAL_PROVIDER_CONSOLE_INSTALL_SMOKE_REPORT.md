# Final Provider Console Install Smoke Report

Generated: 2026-06-20 23:42 Asia/Shanghai

## Result

Install smoke for the provider-console arm64 DMG: PASS

DMG:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-chat-artifacts-20260612/generated-artifacts/Local-AI-Orchestrator-final-complete-arm64-provider-console-unsigned.dmg`

## DMG Install Flow

- DMG exists: PASS
- SHA-256 calculated: PASS
- DMG mounted: PASS
- `.app` copied to isolated test Applications directory: PASS
- Copied `.app` size: `300M`
- Standard macOS `open -n` launch: PASS
- Gatekeeper / Intel warning: no Intel warning was observed by shell-level smoke; architecture audit shows no x86_64-only Mach-O.
- DMG detached after smoke: PASS
- Installed-copy recursive architecture audit: PASS, `84` Mach-O files scanned, `0` x86_64-only

## Runtime Smoke

- `/api/health`: PASS
- `/api/ui-ready`: PASS
- Runtime root: App Data
  `/Users/johnwick/Library/Application Support/com.dreaminmaster.local-ai-orchestrator`
- Packaged mode: PASS
- App data paths: PASS
- Sidecar started from bundled onedir resource: PASS
- App-owned sidecar exited after App quit: PASS
- Port 8422 residue: none
- Port 8423 residue: none

## Provider Workspace Console

Script:

`scripts/e2e_provider_workspace_console.py`

Result: PASS

Checks:

- Claude, ChatGPT, Gemini, Kimi, and Doubao console rows are exposed.
- Project-specific App Data profile paths are returned.
- Console summary counts are present.
- No live prompt was sent during install smoke.

## Local Task Smoke

Real-project packaged task:

- Task id: `real-643fdb54af`
- Final status: PASS
- External AI calls: `0`
- Final report: generated
- Realtime events: PASS, `37` events recorded

## ImportError Runtime Entry Verification

Broken ImportError project:

- Task id: `real-6b81cbf734`
- Final status: FAILED
- Failure reason: `verification_failed`
- Expected behavior: PASS for regression check, because `compileall` passed but `python3 main.py` failed with `ModuleNotFoundError`.

Healthy runtime-entry project:

- Task id: `real-7357727e7f`
- Final status: PASS
- `python3 -m compileall -q .`: PASS
- `python3 main.py`: PASS

## Routing Safety

Routing decisions during smoke:

- `allow_external=false`: selected `lmstudio`
- `allow_external=true`, user not confirmed: selected `lmstudio`
- `allow_external=true`, user confirmed: selected `lmstudio`

Unverified web providers were not selected for automatic routing.

## Conclusion

The provider console, short-answer quality fixes, and ImportError runtime-entry verification are present in the packaged App. The new DMG is suitable to replace the previous arm64 self-use DMG as the preferred local main build.
