# Unsigned DMG Smoke Report

Generated: 2026-06-03

## Result

Unsigned DMG smoke: **PASS**

This was a controlled local prototype smoke only. It did not create a signed,
notarized, or publicly distributable macOS release.

## DMG Artifact

- DMG generated: yes
- Path:
  `smoke_artifacts/Local-AI-Orchestrator-unsigned-smoke.dmg`
- Size: approximately `78M`
- Creation tool: macOS `hdiutil`
- Signing: none
- Notarization: none

The DMG was created from a staging directory containing:

- `Local AI Orchestrator.app`
- `Applications` symlink

## Mount Validation

- DMG mounted successfully: yes
- Mount path:
  `/Volumes/Local AI Orchestrator Unsigned Smoke`
- `.app` present in mounted volume: yes
- Applications symlink present: yes

## Temporary Install Validation

The app was copied from the mounted DMG to:

```text
smoke_install/Applications/Local AI Orchestrator.app
```

- Copy succeeded: yes
- Copied app size: approximately `82M`
- Real `/Applications` was not modified.

## Gatekeeper And Security Result

Read-only security checks reported:

```text
codesign: code object is not signed at all
spctl: rejected
source=no usable signature
```

No observable GUI Gatekeeper prompt appeared during this local launch. No
security policy was changed, no `sudo` was used, and no quarantine attribute
was removed.

This local launch result does not imply that another Mac, or a downloaded copy
with quarantine metadata, will open without a Gatekeeper warning.

## First Launch Runtime Validation

The copied app launched successfully.

- App process started: yes
- packaged WebView created: PASS
- bundled frontend readiness: PASS
- health panel rendered: PASS
- desktop shell mode: `packaged / tauri`
- onedir backend sidecar started: PASS
- `http://127.0.0.1:8422/api/health`: PASS
- `http://localhost:8422/api/health`: PASS
- `/api/ui-ready`: PASS
- app data directory exists: yes
- `runtime/logs/` exists: yes

## Shutdown And Cleanup

- App quit requested: yes
- app-owned sidecar exited: PASS
- final port `8422` listener: none
- residual app or sidecar processes: none
- DMG unmounted: yes
- `smoke_install/` removed: yes
- temporary DMG staging directory removed: yes
- real app data was not deleted

The DMG artifact remains under `smoke_artifacts/` and must not be committed.

## Important Prototype Limitation

The temporary Applications test directory was inside the workspace-dev tree.
The Rust launcher therefore still found the workspace-known onedir backend
sidecar path.

This smoke proves:

- DMG creation and mounting
- app copy flow
- copied app launch
- frontend and backend runtime behavior
- shutdown cleanup

It does not yet prove that the app can run completely independently of the
source workspace. A formal DMG must include the complete onedir sidecar tree
inside App Bundle resources and resolve that installed resource path.

## Static Validation

- `node --check frontend/app.js`: PASS
- `.build-venv/bin/python scripts/health_check.py`: PASS
- `.build-venv/bin/python scripts/beta_validation.py`: PASS, live Claude skipped

## Why This Is Still Not A Release Package

- app is unsigned
- app is not notarized
- Gatekeeper assessment is rejected
- complete onedir sidecar is not yet bundled as an installed app resource
- no clean-machine validation
- no formal DMG layout or release metadata
- no updater
- no public support or recovery flow

## Recommendation

Proceed to formal DMG design, not formal release.

The next design must focus on:

- bundling the complete onedir sidecar tree inside the app
- launching sidecar resources without a workspace path
- signing order for nested binaries and libraries
- Gatekeeper and notarization readiness
- clean-machine installation and removal validation

## Portable Independence Follow-Up

Generated: 2026-06-03

The earlier workspace dependency has been removed from packaged runtime:

- complete onedir sidecar is bundled under App Bundle resources
- packaged launcher selects `bundled_onedir_resource`
- packaged project root and working directory use app data
- runtime, settings, database, and Playwright paths use app data
- isolated DMG copy launched outside workspace-dev
- health and main logs contained no workspace-dev path

Portable independence smoke: **PASS**

See `DMG_INDEPENDENCE_SMOKE_REPORT.md`.
