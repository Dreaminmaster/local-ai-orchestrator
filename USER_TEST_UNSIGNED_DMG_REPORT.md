# User Test Unsigned DMG Report

Generated: 2026-06-03

## Result

User-test unsigned DMG smoke: **PASS**

The current unsigned DMG can be mounted, copied to an isolated test
Applications directory, launched, used for first-run support actions, and
closed without leaving the backend sidecar or port `8422` behind.

## Artifact

```text
/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/
user_test_artifacts/Local-AI-Orchestrator-user-test-unsigned.dmg
```

- DMG size: approximately `170M`
- format: compressed read-only UDIF (`UDZO`)
- signing: none
- notarization: none

## Mount And Copy

- DMG mount: PASS
- mounted App present: PASS
- Applications symlink present: PASS
- copy to isolated test Applications directory: PASS
- copied App size: approximately `312M`
- complete bundled onedir sidecar present: PASS

The smoke test did not write to the real `/Applications` directory.

## Gatekeeper

Gatekeeper assessment:

```text
rejected
source=no usable signature
```

This is expected for the unsigned test artifact. No system security policy was
changed, no `sudo` command was used, and no Gatekeeper bypass was attempted.

## First Run Experience

- copied App launch: PASS
- bundled frontend load: PASS
- First Run status panel present: PASS
- `/api/health`: PASS
- `/api/ui-ready`: PASS
- frontend loaded: true
- health panel rendered: true
- desktop shell mode: `packaged / tauri`
- app data path uses user app data: PASS
- Project browser missing state available: PASS
- Claude and ChatGPT provider status available: PASS
- LM Studio and Ollama status available: PASS

## App Data And Support Actions

- `GET /api/app-data/status`: PASS
- app data exists: true
- app data writable: true
- `POST /api/app-data/open`: PASS
- `POST /api/diagnostics/export`: PASS
- `POST /api/app-data/clear-cache`: PASS

Diagnostic package generated under the user app data `diagnostics/` directory.
Its entry scan found no browser profiles, cookies, evidence, `.env`, database,
or uploaded files.

## Safe Cache Cleanup

Smoke sentinels confirmed removal of:

- runtime temp cache
- local test reports
- pip cache

Confirmed preserved:

- `settings.json`
- browser profiles
- evidence
- tasks

## Shutdown And Cleanup

- normal App quit: PASS
- app-owned sidecar graceful shutdown: PASS
- copied App process residue: none
- port `8422` listener residue: none
- DMG detach: PASS
- temporary test Applications directory cleanup: PASS
- user app data retained: yes

## User Test Materials

The `user_test_artifacts/` directory includes:

- `README_FIRST_TEST.md`
- `UNSIGNED_MAC_OPEN_GUIDE.md`
- `USER_TEST_CHECKLIST.md`
- `CLEANUP_GUIDE.md`
- `KNOWN_LIMITATIONS.md`

## Conclusion

The artifact is ready for the owner to download, copy, and open as a local
unsigned user-test build.

It is still not a formal release because it is unsigned, not notarized, has no
updater, and has not been validated on a clean second Mac.
