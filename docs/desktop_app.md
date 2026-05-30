# Desktop App Roadmap

The final product is intended to be an independent desktop app, not only a web console.

## Recommended Shell

- Tauri for lightweight desktop distribution
- Electron if broader ecosystem compatibility is required

## Desktop Workbench Layout

- Left: goal and success criteria
- Center: current plan and active execution
- Right: available AI and skills
- Bottom: execution logs
- Side panel: Evidence Board

## Control Modes

1. Observe mode: analyze only, no execution.
2. Confirm mode: confirm every key action.
3. Auto mode: low-risk actions auto-execute, high-risk actions confirm.

## Planned `apps/desktop`

A Tauri or Electron shell can load the existing FastAPI-backed web console.
