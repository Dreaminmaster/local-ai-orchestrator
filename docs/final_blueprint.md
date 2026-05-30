# Final Product Blueprint

This repository is now structured as a final-version blueprint plus runnable MVP.

## Final Product Positioning

The target product is an independent desktop AI task workbench:

- Local model connector
- External AI operator
- Browser automation
- Desktop automation
- File / shell / code tools
- Visual review
- Supervisor
- Evidence Board
- Failure repair
- Final report

## What is runnable now

- FastAPI backend
- Web control console
- SQLite schema
- Local model providers
- Core self-supervised loop
- Built-in Skills
- Evidence recording
- Safety policy skeleton
- Snapshot rollback skeleton

## What is intentionally roadmap

- Full Tauri/Electron packaged desktop app
- Real login-state based web automation for ChatGPT/Claude/Doubao/Kimi
- OS-level accessibility integration
- Isolated sandbox runner
- Human confirmation queue in UI

## Design principle

Do not let the local AI pretend to be omnipotent. Let it detect its capability gaps, call the right tools or stronger AI systems, execute locally, and verify with evidence.
