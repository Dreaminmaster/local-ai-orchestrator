# DMG Prep Plan

## Current Unsigned App Prototype

The local macOS prototype has reached a stable packaged runtime checkpoint:

- Tauri build: PASS
- unsigned `.app` generated: PASS
- onedir backend sidecar startup: PASS
- `/api/health`: PASS
- WebView creation: PASS
- UI auto-readiness and health panel rendering: PASS
- app-owned sidecar shutdown: PASS
- final port `8422` residue: none

The current app is suitable for local prototype testing, but it is not a
formal release package.

## Why This Is Not a Release Package

The prototype is not signed with an Apple Developer ID certificate, is not
notarized by Apple, has no stapled notarization ticket, and has not been
validated as a distributable DMG on a clean Mac.

The current onedir sidecar also uses a development-known path. A formal package
must place the complete onedir backend tree inside the app resources and launch
that installed resource path without depending on the source workspace.

## DMG Contents

An unsigned DMG smoke should contain only:

- `Local AI Orchestrator.app`
- an optional Applications folder shortcut
- a minimal background/layout only if it adds real installation clarity
- optional short README text describing that this is an unsigned prototype

The app bundle must contain:

- the Tauri desktop executable
- the bundled frontend assets
- the complete backend onedir sidecar program files
- only the minimum app icons and metadata required by macOS

## Signing Expectations

Ad-hoc signing can be useful for a local unsigned DMG smoke because it gives the
bundle a consistent local signature after nested files are assembled. It does
not establish developer identity, does not satisfy Gatekeeper for public
distribution, and does not replace Developer ID signing or notarization.

For a future public release:

- sign nested sidecar binaries and libraries first
- sign the main app last
- use a Developer ID Application certificate
- enable hardened runtime where compatible
- notarize the final distributable artifact
- staple the notarization ticket
- verify with `codesign`, `spctl`, and Gatekeeper on a clean Mac

## Gatekeeper Behavior

An unsigned or ad-hoc signed app downloaded from the internet may be blocked or
show a warning that Apple cannot verify the developer. Users may need to use
Finder's Open action or System Settings > Privacy & Security to allow the app.

This is acceptable only for an explicitly labeled local prototype. It is not an
acceptable final onboarding experience.

## First Open Flow

The first-open prototype flow should be:

1. User drags the app to Applications.
2. User opens the app and handles any unsigned prototype Gatekeeper prompt.
3. App initializes its writable app data directories.
4. App starts its own backend sidecar only if no healthy backend is already
   running.
5. WebView loads the bundled frontend and reads `/api/health`.
6. UI explains any missing local prerequisites without silently installing
   them.

The app must not automatically log in to external AI providers or access daily
Chrome or Safari profiles.

## App Data Runtime Initialization

Installed runtime data must be created under:

```text
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/
```

Expected writable structure:

```text
runtime/
runtime/logs/
runtime/tasks/
runtime/evidence/
runtime/test_reports/
browser_profiles/
playwright-browsers/
settings.json
```

The app bundle itself must remain read-only at runtime.

## Playwright Browser Provisioning

Playwright browsers are not bundled in the current prototype.

If Chromium is missing:

- `/api/playwright/status` should report the configured path and missing state
- UI should display `需要安装项目专用浏览器`
- UI should explain that External AI Workspace features are unavailable until
  the project-specific browser is installed
- UI should offer a future download action, but must not auto-download in this
  stage
- the browser path must remain isolated from Codex and other software caches

## Local User Data Cleanup

Removing the app from Applications does not remove user data.

Prototype cleanup should be documented as:

1. Quit Local AI Orchestrator.
2. Confirm its backend sidecar is no longer running.
3. Remove the app from Applications.
4. To remove local app data, delete:

```text
~/Library/Application Support/com.dreaminmaster.local-ai-orchestrator/
```

This cleanup must not delete Python, Git, LM Studio, Codex, browser profiles
owned by other applications, or system Playwright caches.

## Future Signing And Notarization Requirements

Before public distribution:

- Apple Developer Program membership
- Developer ID Application signing identity
- hardened runtime compatibility review
- entitlements review for the Tauri app and sidecar
- nested onedir binaries and libraries signing order
- notarization credentials stored outside the repository
- notarization submission and ticket stapling
- clean-machine Gatekeeper validation
- crash log and startup failure support flow
- versioning and update strategy

## Content That Must Not Enter The DMG

Do not package:

- `runtime/`
- `browser_profiles/`
- `evidence/`
- `test_reports/`
- `.env`
- local databases
- user credentials
- local browser caches
- `.playwright-browsers/` or Playwright browser cache in this stage
- `.build-venv/`
- source `venv/`
- `node_modules/`
- Tauri `target/`
- local build logs

## Recommended Next Step

The next controlled milestone can be an unsigned DMG smoke, provided it remains
clearly labeled as a local prototype. That smoke should validate DMG creation,
drag-to-Applications installation, app launch, app data initialization, sidecar
startup, UI readiness, shutdown cleanup, and Gatekeeper behavior.

It must not be treated as a public release.

## Unsigned DMG Smoke Result

Generated: 2026-06-03

The controlled unsigned DMG smoke passed:

- DMG creation: PASS
- mount: PASS
- temporary copy install: PASS
- copied app launch: PASS
- backend health: PASS
- UI readiness: PASS
- sidecar shutdown: PASS
- cleanup: PASS

Security assessment remained expected for an unsigned prototype:

```text
spctl: rejected
source=no usable signature
```

No security policy was changed and no Gatekeeper bypass was used.

The next formal DMG design step must bundle the complete onedir sidecar tree
inside App resources. The smoke install directory was still inside
workspace-dev, so it did not prove source-workspace independence.

## Portable Independence Result

Generated: 2026-06-03

The complete onedir backend tree is now bundled under App resources, and the
packaged launcher starts it from the installed `.app` instead of the
workspace-dev build directory.

An isolated DMG copy outside workspace-dev passed:

- sidecar startup
- backend health
- app data runtime paths
- UI readiness
- sidecar shutdown
- no port residue
- no workspace-dev path in health or main logs

The artifact can now be treated as a locally movable unsigned DMG prototype.
Formal release preparation may begin, but signing, notarization, clean-machine
testing, and release packaging remain required.
