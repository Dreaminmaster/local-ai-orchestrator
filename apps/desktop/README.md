# Local AI Orchestrator Desktop Dev Shell

This folder contains a Tauri v2 **development shell** for the existing local web product.

It is not a formal installer and does not bundle a Python sidecar binary yet.

## Dev Experience

Expected flow:

1. Run the desktop dev script.
2. The script checks Node, npm, Rust, Cargo, and Tauri CLI.
3. Tauri opens a WebView pointed at `http://127.0.0.1:8422`.
4. `src-tauri/run_dev_backend.sh` checks `/api/health`.
5. If the backend is already healthy, it does not start another backend.
6. If the backend is not healthy, it starts the Python backend with portable env vars.
7. On close, it stops only the backend process that it started itself.

## Commands

macOS/Linux:

```bash
apps/desktop/run_dev.sh
```

Windows:

```powershell
apps\desktop\run_dev_windows.ps1
```

## Portable Env

The dev backend launcher sets:

- `PROJECT_ROOT`
- `PYTHONPATH`
- `PLAYWRIGHT_BROWSERS_PATH`
- `PIP_CACHE_DIR`
- `TMPDIR`

It does not install dependencies.

Python selection:

1. `local-ai-orchestrator-workspace-dev/venv/bin/python`
2. `/Users/johnwick/Documents/codex/local-ai-orchestrator-main/venv/bin/python`

The second option is only a local dev fallback and should be documented in reports.

## Tauri Config

- `devUrl`: `http://127.0.0.1:8422`
- `bundle.active`: `false`
- no DMG/EXE/MSI config
- no PyInstaller sidecar binary
- no `externalBin` configured yet

## Future Formal Sidecar

The real packaging phase can later:

- turn the Python backend into a sidecar binary,
- configure `bundle.externalBin`,
- add Tauri shell permissions only for the bundled sidecar,
- build DMG/EXE/MSI,
- sign and notarize release artifacts.

This dev shell intentionally avoids those steps.

