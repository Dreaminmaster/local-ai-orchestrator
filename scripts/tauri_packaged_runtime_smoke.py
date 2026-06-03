#!/usr/bin/env python3
"""Controlled packaged Tauri runtime smoke for the local unsigned macOS app."""

from __future__ import annotations

import argparse
import http.client
import json
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = (
    ROOT
    / "apps/desktop/src-tauri/target/release/bundle/macos/Local AI Orchestrator.app"
)
PORT = 8422
FRONTEND_ASSETS = {
    "index.html": ROOT / "frontend/index.html",
    "app.js": ROOT / "frontend/app.js",
    "style.css": ROOT / "frontend/style.css",
}
APP_DATA_LOGS = (
    Path.home()
    / "Library/Application Support/com.dreaminmaster.local-ai-orchestrator/runtime/logs"
)


def port_open(host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def probe_json(host: str, path: str, timeout: float = 3.0) -> tuple[bool, dict | None, str]:
    connection = http.client.HTTPConnection(host, PORT, timeout=timeout)
    try:
        connection.request("GET", path, headers={"Connection": "close"})
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        data = json.loads(body) if body else {}
        return response.status == 200, data, ""
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"
    finally:
        connection.close()


def app_processes() -> list[str]:
    proc = subprocess.run(
        ["ps", "-axo", "pid,ppid,stat,command"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [
        line.strip()
        for line in proc.stdout.splitlines()
        if "Local AI Orchestrator.app/Contents/MacOS/local-ai-orchestrator-" in line
        or "local-ai-orchestrator-backend-dir/local-ai-orchestrator-backend" in line
    ]


def log_tail(path: Path, lines: int = 40) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]


def log_contains(path: Path, marker: str) -> bool:
    if not path.exists():
        return False
    return marker in path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke the packaged Tauri app runtime")
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--startup-timeout", type=int, default=240)
    parser.add_argument(
        "--forbid-path",
        default="",
        help="fail if this path appears in health data or the desktop main log",
    )
    args = parser.parse_args()

    app = args.app.expanduser().resolve()
    if not app.exists():
        print(f"FAIL app_missing={app}")
        return 2
    if port_open():
        print("FAIL port_8422_already_open=true")
        return 2

    print(f"app={app}")
    subprocess.run(["open", "-n", str(app)], check=True)
    print("app_open_requested=true")

    health_127 = None
    health_localhost = None
    ui_ready = None
    frontend_assets = {
        name: {"exists": path.exists(), "path": str(path)}
        for name, path in FRONTEND_ASSETS.items()
    }
    health_errors: list[str] = []
    health_ready_at = None
    deadline = time.monotonic() + args.startup_timeout
    while time.monotonic() < deadline:
        ok_127, data_127, error_127 = probe_json("127.0.0.1", "/api/health")
        if error_127:
            health_errors.append(f"127.0.0.1={error_127}")
        if ok_127:
            health_127 = data_127
            health_ready_at = health_ready_at or time.monotonic()
            ok_local, data_local, error_local = probe_json("localhost", "/api/health")
            health_localhost = data_local if ok_local else {"error": error_local}
            ok_ui, data_ui, error_ui = probe_json("127.0.0.1", "/api/ui-ready")
            ui_ready = data_ui if ok_ui else {"error": error_ui}
            if ok_ui and data_ui and data_ui.get("ready"):
                break
            if (
                all(item.get("exists") for item in frontend_assets.values())
                and time.monotonic() - health_ready_at >= 5
            ):
                break
        time.sleep(1)

    print(f"health_127={json.dumps(health_127, ensure_ascii=False)}")
    print(f"health_localhost={json.dumps(health_localhost, ensure_ascii=False)}")
    print(f"frontend_assets={json.dumps(frontend_assets, ensure_ascii=False)}")
    print(f"ui_ready={json.dumps(ui_ready, ensure_ascii=False)}")
    print(f"processes={json.dumps(app_processes(), ensure_ascii=False)}")
    if health_127 is None:
        print(f"health_errors_tail={json.dumps(health_errors[-5:], ensure_ascii=False)}")
        for name in (
            "desktop-main.log",
            "desktop-sidecar-stdout.log",
            "desktop-sidecar-stderr.log",
        ):
            path = APP_DATA_LOGS / name
            print(f"{name}_path={path}")
            print(f"{name}_tail={json.dumps(log_tail(path), ensure_ascii=False)}")

    subprocess.run(
        ["osascript", "-e", 'tell application "Local AI Orchestrator" to quit'],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print("app_quit_requested=true")

    shutdown_deadline = time.monotonic() + 20
    while time.monotonic() < shutdown_deadline:
        if not port_open() and not app_processes():
            break
        time.sleep(0.5)

    residual_port = port_open()
    residual_processes = app_processes()
    main_log = APP_DATA_LOGS / "desktop-main.log"
    webview_created = log_contains(main_log, "webview_created")
    webview_load_started = log_contains(main_log, "webview_load_start")
    sidecar_shutdown_done = log_contains(main_log, "sidecar_shutdown_done")
    forbidden_path = args.forbid_path
    forbidden_in_health = bool(
        forbidden_path
        and forbidden_path
        in json.dumps({"health_127": health_127, "health_localhost": health_localhost})
    )
    forbidden_in_main_log = bool(forbidden_path and log_contains(main_log, forbidden_path))
    print(f"residual_port_8422={str(residual_port).lower()}")
    print(f"residual_processes={json.dumps(residual_processes, ensure_ascii=False)}")
    print(f"webview_created={str(webview_created).lower()}")
    print(f"webview_load_started={str(webview_load_started).lower()}")
    print(f"sidecar_shutdown_done={str(sidecar_shutdown_done).lower()}")
    print(f"forbidden_path={forbidden_path}")
    print(f"forbidden_in_health={str(forbidden_in_health).lower()}")
    print(f"forbidden_in_main_log={str(forbidden_in_main_log).lower()}")

    core_ready = bool(
        health_127
        and health_127.get("ok")
        and health_localhost
        and health_localhost.get("ok")
        and frontend_assets
        and all(item.get("exists") for item in frontend_assets.values())
        and webview_created
        and webview_load_started
        and sidecar_shutdown_done
        and not forbidden_in_health
        and not forbidden_in_main_log
        and not residual_port
        and not residual_processes
    )
    ui_auto_ready = bool(
        ui_ready and ui_ready.get("ready") and ui_ready.get("health_panel_rendered")
    )
    if core_ready and ui_auto_ready:
        final_status = "PASS"
    elif core_ready:
        final_status = "PASS_WITH_MANUAL_UI_CHECK"
    else:
        final_status = "FAIL"
    print(f"sidecar_runtime={'PASS' if core_ready else 'FAIL'}")
    print(f"ui_auto_ready={'PASS' if ui_auto_ready else 'UNKNOWN'}")
    print(f"ui_manual_check_required={str(core_ready and not ui_auto_ready).lower()}")
    print(f"final_status={final_status}")
    return 0 if core_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
