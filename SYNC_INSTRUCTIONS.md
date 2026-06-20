# Sync Instructions

## Baseline

- Repository: `Dreaminmaster/local-ai-orchestrator`
- Local baseline commit: `d42701a30b144ea13c0661b74a20995ef350d006`
- Baseline tag: `v0.1.1-beta-kernel`
- This package is a local first-run experience checkpoint.
- Do not push or tag without explicit user confirmation.

## Apply The Patch

```bash
git checkout v0.1.1-beta-kernel
git checkout -b first-run-experience
git apply first_run_experience.patch
```

The patch is a source and documentation backup. It includes the unsigned
portable DMG prototype work plus the first-run status page, app data APIs,
diagnostic export, and safe cache cleanup. It does not include local runtime
data, build environments, browser profiles, binaries, `.app` bundles, or Tauri
build output.

## Recommended Validation

Run non-live checks first:

```bash
python3 scripts/health_check.py
python3 scripts/beta_validation.py
node --check frontend/app.js
```

For the macOS prototype build, use the documented project-local build
environment and onedir backend flow. Do not run provider live tests as part of
the sync validation.

Do not commit, push, or tag until the user explicitly requests synchronization.

## Do Not Commit

- `.build-venv/`
- `runtime/`
- `venv/`
- `.env`
- `.playwright-browsers/`
- browser profiles
- evidence
- local test reports
- `apps/desktop/node_modules/`
- `apps/desktop/src-tauri/target/`
- generated `.app` or DMG files
- backend binary or onedir binary directory
- local databases
