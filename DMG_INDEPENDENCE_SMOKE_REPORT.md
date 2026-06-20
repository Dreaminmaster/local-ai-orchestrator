# DMG Portable Independence Smoke Report

Generated: 2026-06-03

## Result

DMG portable independence smoke: **PASS**

The unsigned DMG prototype can now run from an isolated location without using
the workspace-dev backend sidecar path.

## Path Dependency Audit

Before this change, packaged runtime logs showed:

- sidecar strategy: `onedir_dev_known_path`
- sidecar executable under:
  `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/`
- `--project-root` set to workspace-dev
- sidecar working directory set to workspace-dev

These were real packaged-runtime dependencies and prevented independent DMG
operation.

Dev-only references that remain acceptable:

- `apps/desktop/src-tauri/run_dev_backend.sh`
- `LOCAL_AI_PROJECT_ROOT` override for explicit development use
- project-local runtime behavior when running Python dev mode

## App Bundle Onedir Sidecar

The complete PyInstaller onedir sidecar is now bundled as a Tauri resource:

```text
Local AI Orchestrator.app/Contents/Resources/bin/
  local-ai-orchestrator-backend-dir/
    local-ai-orchestrator-backend
    _internal/
```

Validation:

- target executable present: PASS
- `_internal` dependency directory present: PASS
- sidecar executable can find adjacent dependencies: PASS
- App Bundle size: approximately `312M`
- App Bundle string scan found no workspace-dev absolute path: PASS

Tauri `externalBin` remains present for the earlier onefile build path, but the
packaged launcher now prioritizes `bundled_onedir_resource`.

## Packaged Runtime Path Model

Packaged mode now uses:

```text
project_root:
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator

runtime_dir:
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime

playwright_browsers_path:
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/playwright-browsers

settings.json:
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/settings.json

database:
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime/orchestrator.db
```

No runtime data is written into the App Bundle.

## Isolated DMG Test

The DMG was copied to:

```text
/Users/johnwick/Documents/codex/dmg_independence_smoke/
```

The app was installed to:

```text
/Users/johnwick/Documents/codex/dmg_independence_smoke/Applications/
Local AI Orchestrator.app
```

The test environment explicitly unset `LOCAL_AI_PROJECT_ROOT` and rejected any
health or main-log reference to:

```text
/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev
```

## Runtime Result

- DMG generation: PASS
- DMG mount: PASS
- isolated app copy: PASS
- isolated app launch: PASS
- sidecar strategy: `bundled_onedir_resource`
- sidecar path inside isolated App Bundle: PASS
- `/api/health`: PASS
- `/api/health.project_root` uses app data: PASS
- `/api/health.runtime_dir` uses app data: PASS
- `/api/health.playwright_browsers_path` uses app data: PASS
- forbidden workspace path in health: false
- forbidden workspace path in main log: false
- UI readiness: PASS
- sidecar shutdown: PASS
- final port `8422` residue: none

## Cleanup

- isolated app and DMG copy removed: yes
- mounted DMG detached: yes
- temporary staging directory removed: yes
- app data retained: yes
- workspace source directory was not moved or renamed

## Validation

- `node --check frontend/app.js`: PASS
- `.build-venv/bin/python scripts/health_check.py`: PASS
- `.build-venv/bin/python scripts/beta_validation.py`: PASS, live Claude skipped
- `.build-venv/bin/python -m unittest tests/test_runtime_paths_settings_playwright.py`: PASS
- Rust `cargo check`: PASS

## Conclusion

The current artifact can be described as a **locally movable unsigned DMG
prototype**.

It is still not a formal release because it is unsigned, not notarized, not
validated on a clean second Mac, and has no final release packaging, signing,
or updater workflow.

The next stage can enter formal DMG release preparation.

## First Run Product Experience Follow-Up

Generated: 2026-06-03

The packaged app now includes a first run status panel and local support
actions. Packaged smoke verified:

- app data path display and open action
- diagnostics export
- safe cache cleanup
- Playwright browser missing notice
- health and UI readiness
- sidecar shutdown and no port residue

The new APIs continue to use app data paths and do not reintroduce a
workspace-dev dependency.

See `FIRST_RUN_EXPERIENCE_REPORT.md`.
