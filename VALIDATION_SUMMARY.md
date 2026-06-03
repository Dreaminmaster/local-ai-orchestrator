# Validation Summary

## Stable Checkpoint

The unsigned macOS app prototype reached the following local validation state:

- Tauri build: PASS
- onedir backend sidecar: PASS
- packaged sidecar startup: PASS
- `/api/health`: PASS
- WebView created: PASS
- UI auto-readiness: PASS
- health panel rendered: PASS
- sidecar shutdown: PASS
- final port `8422` residue: none
- packaged runtime smoke final status: PASS

## Supporting Non-Live Checks

Previously completed in this workspace:

- `health_check.py`: PASS
- `beta_validation.py`: PASS, live Claude skipped
- repair matrix: 10/10 PASS
- `node --check frontend/app.js`: PASS
- Claude extractor tests: PASS
- workspace recovery tests: PASS
- workspace login state tests: PASS
- answer quality tests: PASS
- pending external AI resume tests: PASS
- runtime paths, settings, and Playwright status tests: PASS
- Rust `cargo check`: PASS

## Runtime Smoke Notes

- PyInstaller onefile packaged startup was opaque and unreliable.
- PyInstaller onedir is the recommended v0.2.x sidecar prototype direction.
- The final UI readiness issue was caused by navigating away from Tauri
  `frontendDist` to a frozen backend root that returned `404`.
- Keeping the bundled frontend loaded allowed `/api/ui-ready` to report:
  `ready=true`, `frontend_loaded=true`, and `health_panel_rendered=true`.

## Out Of Scope

No live Claude or other provider test was run for this checkpoint.

## Unsigned DMG Smoke

- unsigned DMG creation: PASS
- DMG mount: PASS
- temporary app copy: PASS
- copied app launch: PASS
- backend health: PASS
- UI readiness: PASS
- sidecar shutdown: PASS
- final port residue: none
- Gatekeeper assessment: rejected, `no usable signature`

No signing, notarization, updater, or public release artifact was created.

## DMG Portable Independence

- complete onedir sidecar bundled in App resources: PASS
- isolated DMG copy outside workspace-dev: PASS
- bundled sidecar launch strategy: `bundled_onedir_resource`
- `/api/health` app data project root: PASS
- app data runtime and Playwright paths: PASS
- workspace-dev path absent from health and main logs: PASS
- UI readiness: PASS
- sidecar shutdown: PASS
- final port residue: none

The artifact is a locally movable unsigned DMG prototype.

## First Run Experience And Local Support

- first-run setup status panel: PASS
- packaged app data path display: PASS
- `GET /api/app-data/status`: PASS
- `POST /api/app-data/open`: PASS
- `POST /api/diagnostics/export`: PASS
- diagnostic package exclusion scan: PASS
- `POST /api/app-data/clear-cache`: PASS
- settings, profiles, evidence, and tasks preservation: PASS
- Playwright Chromium missing-state UI: PASS
- packaged `/api/health`: PASS
- packaged `/api/ui-ready`: PASS
- sidecar shutdown and final port residue: PASS

Focused offline tests:

- app data and diagnostics tests: PASS
- runtime paths, settings, and Playwright status tests: PASS
- `node --check frontend/app.js`: PASS

No browser download, provider live test, profile reset, signing, notarization,
updater, push, or tag was performed.
