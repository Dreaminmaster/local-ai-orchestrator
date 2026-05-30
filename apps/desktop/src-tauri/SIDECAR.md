# Python Backend Sidecar Plan

Alpha desktop shell uses Tauri dev mode only.

Current behavior:

- `beforeDevCommand` in `tauri.conf.json` runs `cd ../.. && python run.py`
- WebView opens `http://127.0.0.1:8422`
- `bundle.active` is intentionally `false`

Not doing yet:

- no dmg/msi
- no Python binary bundling
- no production updater

Next production step:

1. Build a Python backend binary with PyInstaller or uv/standalone Python.
2. Register it as a Tauri sidecar.
3. Make the desktop app own backend lifecycle.
4. Add health check / restart if backend crashes.
