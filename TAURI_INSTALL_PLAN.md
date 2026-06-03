# Tauri Install Plan

Generated: 2026-06-02T18:08:00+08:00

Workspace:

`/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev`

Scope: this is only a Rust/Cargo/Tauri development environment plan. No installation was performed, no live Claude run was performed, no provider test was performed, and no DMG/EXE/MSI or PyInstaller work is included.

## 1. Current Environment Check

| Check | Result |
|---|---|
| `node --version` | `v25.9.0` |
| `npm --version` | `11.12.1` |
| `rustc --version` | missing, `command not found` |
| `cargo --version` | missing, `command not found` |
| `xcode-select -p` | `/Applications/Xcode.app/Contents/Developer` |
| `xcodebuild -version` | `Xcode 26.4.1`, build `17E202` |
| `npx --version` | `11.12.1` |
| `npm exec tauri -- --version` from `apps/desktop` | not runnable yet, `could not determine executable to run` |
| `apps/desktop/node_modules` | missing |

`apps/desktop/package.json` already contains Tauri dev scripts:

```json
{
  "scripts": {
    "dev": "tauri dev",
    "build": "tauri build"
  },
  "devDependencies": {
    "@tauri-apps/cli": "latest"
  }
}
```

Conclusion: Node/npm and Xcode are present. Rust/Cargo are missing. Tauri CLI is declared as a project dev dependency but cannot run until `apps/desktop/npm install` creates `apps/desktop/node_modules`.

## 2. What Needs To Be Installed

macOS requirements:

- Xcode Command Line Tools: likely already satisfied because `xcode-select -p` points to `/Applications/Xcode.app/Contents/Developer` and `xcodebuild -version` works. If future Tauri/Rust builds complain about missing command line tools, run Apple’s CLT installer flow, but do not do that unless needed.
- Rust / Cargo: required. Install with official `rustup`, which provides both `rustc` and `cargo`.
- Tauri CLI: global install is not required. Prefer project-local npm dev dependency from `apps/desktop/package.json` and run it through `npm run dev` or `npm exec tauri`.
- `apps/desktop` npm dependencies: required. Run `npm install` inside `apps/desktop`, which installs `@tauri-apps/cli` into `apps/desktop/node_modules`.
- System WebView dependencies: on macOS, Tauri uses system WebKit/WebView support. Unlike Linux, this does not normally require installing `webkit2gtk` packages.

Recommended approach: install only Rust/Cargo as development tools, then install desktop npm dependencies only inside `apps/desktop`.

## 3. Installation Location Notes

- Xcode / Xcode Command Line Tools install into Apple system developer tool locations such as `/Applications/Xcode.app/Contents/Developer` or `/Library/Developer/CommandLineTools`.
- Rustup usually installs into `~/.rustup`.
- Cargo usually installs into `~/.cargo`.
- Cargo binaries are usually placed under `~/.cargo/bin`.
- `apps/desktop` npm dependencies install into `apps/desktop/node_modules`.
- These are not project portable dependencies. Deleting `/Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev` will not delete Rust/Cargo or Xcode developer tools.
- They are developer tools and should not affect Python, Git, LM Studio, Codex, or the portable runtime directories used by this project.
- Rust/Cargo should not be copied into the project portable folder.

## 4. Uninstall Notes

Rust/Cargo:

```bash
rustup self uninstall
```

This removes the rustup-managed toolchains from `~/.rustup` and Cargo binaries/config from `~/.cargo`, subject to rustup’s prompts.

Project npm dependencies:

```bash
rm -rf apps/desktop/node_modules
rm -f apps/desktop/package-lock.json
```

Only run this from the project checkout when intentionally cleaning desktop npm dependencies.

Global Tauri CLI, if ever installed globally:

```bash
npm uninstall -g @tauri-apps/cli
```

This plan does not recommend global Tauri CLI installation.

Xcode / Command Line Tools:

- Do not casually delete Xcode or Command Line Tools.
- Other developer tools may depend on them.
- If removal is ever necessary, use Apple-supported uninstall/update flows and confirm first.

## 5. Recommended Installation Method

Preferred sequence after explicit user confirmation:

1. Install Rust/Cargo using official rustup.
2. Do not install Tauri CLI globally.
3. Run `npm install` only inside `apps/desktop`.
4. Use the project-local Tauri CLI through `npm run dev`.
5. Avoid `brew install` for this stage unless a specific missing dependency is proven necessary.

Expected commands after confirmation:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then, after opening a new shell or sourcing Cargo env:

```bash
rustc --version
cargo --version
cd /Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/apps/desktop
npm install
npm run dev
```

No global npm install should be needed for Tauri.

## 6. Post-Install Verification Commands

From any shell:

```bash
rustc --version
cargo --version
```

Install desktop dependencies:

```bash
cd /Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/apps/desktop
npm install
```

Run Tauri dev using the actual script currently defined in `apps/desktop/package.json`:

```bash
cd /Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/apps/desktop
npm run dev
```

Verify backend health:

```bash
curl http://127.0.0.1:8422/api/health
```

Backend process checks:

```bash
lsof -nP -iTCP:8422 -sTCP:LISTEN
```

Expected:

- The WebView opens the product UI.
- `/api/health` returns `"ok": true`.
- Only one backend listens on port `8422`.
- If an existing healthy backend is already running, the Tauri launcher should not start a duplicate backend.
- After closing Tauri, check whether a backend remains on `8422`.
- If the dev launcher started the backend itself, it should stop that backend on exit.
- If the backend was already running before Tauri started, it should not be killed by Tauri shutdown.

## 7. Risks And Boundaries

- This step is for a developer environment only, not a normal-user installer.
- It does not build DMG, EXE, MSI, or any signed desktop package.
- It does not run PyInstaller or create a Python sidecar binary.
- It does not automatically handle Claude login.
- It does not run live Claude.
- It does not test ChatGPT, Doubao, Kimi, or Gemini.
- It does not touch daily Chrome or Safari profiles.
- It does not reset project browser profiles.
- It does not commit or package `runtime/`, `venv/`, `.env`, `.playwright-browsers/`, browser profiles, evidence, or local test reports.
- Rust/Cargo will not be placed inside the project portable folder.
- A previous `npm exec tauri -- --version` check wrote an npm diagnostic log under `~/.npm/_logs`; this was a command probe, not a dependency installation.

## 8. Next Plan After Installation Confirmation

A. After explicit user confirmation, install Rust/Cargo and the project-local Tauri dev dependency setup.

B. Run Tauri dev smoke:

```bash
cd /Users/johnwick/Documents/codex/local-ai-orchestrator-workspace-dev/apps/desktop
npm run dev
```

C. Confirm the Tauri WebView opens the product UI.

D. Confirm backend startup and shutdown behavior:

- no duplicate backend
- `/api/health` works
- Tauri shutdown does not kill unrelated Python processes
- Tauri shutdown cleans up only the backend it started itself

E. Only after dev shell is stable, design the Python backend sidecar binary approach.

F. Only after sidecar design is validated, start formal installer packaging work.

## Recommendation

Current missing tools:

- Rust/Cargo
- installed `apps/desktop/node_modules` containing the project-local Tauri CLI

Recommendation: yes, installing the Rust/Cargo developer environment is the appropriate next step if the goal is to actually run the Tauri desktop shell. Do it only after explicit confirmation, using rustup plus project-local npm dependencies, not global Tauri CLI.
