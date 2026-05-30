# Desktop Shell Plan

Preferred path: **Tauri + Python sidecar**.

Goal:

1. User opens desktop app.
2. App starts Python FastAPI backend as sidecar: `python run.py`.
3. App loads `http://127.0.0.1:8422` in the WebView.
4. Closing app stops backend.

Why Tauri first:

- lighter than Electron
- good system integration
- suitable wrapper around existing Web UI

Alternative: Electron + Python backend if WebView / plugin ecosystem becomes more important.

Next implementation steps:

```bash
cd apps/desktop
npm install
npm create tauri-app@latest .
```

Then configure Tauri sidecar to launch project root `run.py`.
