# Release DMG Preparation Plan

## Current Unsigned Portable DMG Status

The macOS prototype has reached a locally movable unsigned DMG checkpoint:

- DMG generation and mount: PASS
- app copy from DMG: PASS
- complete PyInstaller onedir sidecar bundled in App resources: PASS
- isolated app launch outside workspace-dev: PASS
- backend `/api/health`: PASS
- bundled frontend and UI readiness: PASS
- app-owned sidecar shutdown: PASS
- final port `8422` residue: none
- runtime, settings, database, and Playwright paths use app data
- health and desktop logs contain no workspace-dev dependency

The packaged launcher uses `bundled_onedir_resource`.

## Why This Is Not A Formal Release

The current artifact is intentionally unsigned and not notarized. Gatekeeper
assessment reports `rejected` with `no usable signature`.

It has not yet been validated on a clean second Mac, does not have a formal
support or diagnostics flow, and has no release signing, notarization,
versioning, updater, or compatibility matrix.

## First Launch User Flow

The intended first-launch flow is:

1. User opens the DMG.
2. User drags Local AI Orchestrator into Applications.
3. User launches the app.
4. App initializes its user-writable app data directories.
5. App starts its bundled backend sidecar if no healthy backend is already
   running.
6. Bundled frontend loads and renders backend health.
7. UI reports missing local prerequisites such as LM Studio or Playwright
   Chromium without silently installing them.
8. User opens an External AI Workspace only when needed and handles login or
   verification manually.

The app must not access daily Chrome or Safari profiles.

## Unsigned Gatekeeper Explanation

The current unsigned prototype may be blocked when downloaded or copied to
another Mac. Users may see warnings that the developer cannot be verified.

For internal prototype testing, documentation may explain this limitation, but
the app must not disable Gatekeeper, clear quarantine attributes automatically,
or ask users to weaken system security.

Public distribution requires Developer ID signing and notarization.

## App Data Directory Structure

Installed app data lives under:

```text
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/
```

Expected structure:

```text
settings.json
playwright-browsers/
runtime/
runtime/orchestrator.db
runtime/logs/
runtime/tasks/
runtime/browser_profiles/
runtime/evidence/
runtime/test_reports/
runtime/tmp/
```

The App Bundle remains read-only at runtime. User profiles, evidence, reports,
credentials, and local databases must never be placed inside the DMG.

## Settings Initialization

On first launch:

1. Resolve the app data directory.
2. Create required runtime directories.
3. Create `settings.json` if it does not exist.
4. Populate non-secret defaults such as LM Studio endpoint, Ollama endpoint,
   Playwright browser path, provider enablement, and authorization defaults.
5. Never write API keys or plaintext secrets into `settings.json`.
6. Preserve existing user settings on upgrades.

Development `.env` support may remain as a dev fallback, but `.env` must not be
packaged in the release DMG.

## Playwright Browser Missing UX

Playwright browsers are not bundled in the current DMG.

When Chromium is missing:

- `/api/playwright/status` reports the configured path and missing state
- UI displays `需要安装项目专用浏览器`
- External AI Workspace actions explain why they are unavailable
- UI offers a future explicit download action
- no browser download starts automatically
- downloaded browsers must remain isolated under app data

## Local Data Cleanup And Reset

The product should offer two levels of cleanup:

### Reset External AI Workspace

- close the selected workspace
- remove only that provider's project-owned browser profile after confirmation
- do not touch daily Chrome or Safari profiles

### Remove All Local App Data

After quitting the app and confirming the sidecar is stopped, remove:

```text
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/
```

This must not remove Python, Git, LM Studio, Codex, system browser data, or
other Playwright caches.

## Diagnostic Package Export

Add a future user-controlled diagnostic export action that creates a zip with:

- app version and platform
- `/api/health` snapshot
- Playwright status snapshot
- sanitized `settings.json`
- desktop main log
- sidecar stdout and stderr logs
- recent task metadata
- recent error summaries

The diagnostic package must exclude:

- browser profiles
- credentials and cookies
- prompt or answer content unless explicitly approved
- evidence screenshots unless explicitly approved
- API keys or secrets
- local databases by default

## Future Signing And Notarization

Formal macOS release preparation requires:

- Apple Developer Program membership
- Developer ID Application certificate
- hardened runtime compatibility review
- entitlements review
- nested onedir binary and library signing order
- signing the main app last
- notarization submission credentials stored outside the repository
- notarization ticket stapling
- `codesign` verification
- `spctl` Gatekeeper verification
- clean-machine launch validation

No signing or notarization is performed in this stage.

## Formal DMG Structure

The formal DMG should contain only:

- `Local AI Orchestrator.app`
- Applications folder shortcut
- optional restrained background and layout
- optional short release README or support link

The App Bundle should contain:

- Tauri desktop executable
- bundled frontend
- complete onedir backend sidecar tree
- required icons and metadata

The DMG must not contain:

- runtime data
- browser profiles
- evidence
- test reports
- `.env`
- local databases
- Playwright browser cache in the current release plan
- build environments
- source code or development scripts

## Windows Follow-Up Plan

Windows work should follow after the macOS release path is stable:

1. Build a Windows-compatible backend onedir sidecar.
2. Use the Windows target triple and Tauri resource layout.
3. Store runtime data under `%APPDATA%/Local AI Orchestrator/`.
4. Validate backend lifecycle and port conflict behavior.
5. Validate Playwright browser provisioning under app data.
6. Design an unsigned MSI or installer smoke only after portable runtime
   independence is proven.
7. Add Windows code signing before public distribution.

## Recommended Next Milestone

The next milestone is formal DMG release preparation, focused on:

- clean-machine validation
- first-launch UX
- diagnostics export design
- local data reset UX
- signing and notarization readiness review

It is not yet a formal release build.
