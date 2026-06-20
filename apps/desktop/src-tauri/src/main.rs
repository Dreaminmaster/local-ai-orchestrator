use std::{
    fs::OpenOptions,
    io::{Read, Write},
    net::TcpStream,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

use tauri::{Manager, RunEvent};

const HEALTH_HOST: &str = "127.0.0.1";
const HEALTH_PORT: u16 = 8422;
const HEALTH_URL: &str = "http://127.0.0.1:8422/api/health";
const BACKEND_BASE_NAME: &str = "local-ai-orchestrator-backend";
const BACKEND_TARGET: &str = "aarch64-apple-darwin";
const BACKEND_ONEDIR_NAME: &str = "local-ai-orchestrator-backend-dir";

#[derive(Default)]
struct SidecarLifecycle {
    child: Option<Child>,
    started_by_app: bool,
    main_log_path: Option<PathBuf>,
}

type SidecarState = Arc<Mutex<SidecarLifecycle>>;

fn log_event(state: &SidecarState, event: &str, detail: &str) {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default();
    let line = format!("{timestamp} {event} {detail}\n");
    print!("[desktop] {event} {detail}\n");
    let path = state
        .lock()
        .ok()
        .and_then(|guard| guard.main_log_path.clone());
    if let Some(path) = path {
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
            let _ = file.write_all(line.as_bytes());
        }
    }
}

fn health_ok() -> bool {
    let Ok(mut stream) = TcpStream::connect_timeout(
        &format!("{HEALTH_HOST}:{HEALTH_PORT}")
            .parse()
            .expect("static health socket address must parse"),
        Duration::from_millis(800),
    ) else {
        return false;
    };
    let request = b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
    if stream.write_all(request).is_err() {
        return false;
    }
    let _ = stream.set_read_timeout(Some(Duration::from_millis(800)));
    let mut buffer = [0_u8; 512];
    let Ok(n) = stream.read(&mut buffer) else {
        return false;
    };
    let response = String::from_utf8_lossy(&buffer[..n]);
    response.starts_with("HTTP/1.1 200") || response.starts_with("HTTP/1.0 200")
}

fn wait_for_health(timeout: Duration, state: &SidecarState) -> bool {
    log_event(state, "backend_health_check_start", HEALTH_URL);
    let start = Instant::now();
    while start.elapsed() < timeout {
        if health_ok() {
            log_event(state, "backend_health_check_result", "ok=true");
            return true;
        }
        thread::sleep(Duration::from_millis(300));
    }
    log_event(
        state,
        "backend_health_check_result",
        "ok=false timeout=true",
    );
    false
}

fn sidecar_candidates(app: &tauri::App, project_root: &Path) -> Vec<(PathBuf, &'static str)> {
    let sidecar_name = format!("{BACKEND_BASE_NAME}-{BACKEND_TARGET}");
    let mut candidates = Vec::new();

    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push((
            resource_dir
                .join("bin")
                .join(BACKEND_ONEDIR_NAME)
                .join(BACKEND_BASE_NAME),
            "bundled_onedir_resource",
        ));
        candidates.push((
            resource_dir.join("bin").join(BACKEND_BASE_NAME),
            "bundled_external_bin",
        ));
        candidates.push((
            resource_dir.join("bin").join(&sidecar_name),
            "bundled_target_external_bin",
        ));
        candidates.push((
            resource_dir.join(BACKEND_BASE_NAME),
            "bundled_resource_external_bin",
        ));
        candidates.push((
            resource_dir.join(&sidecar_name),
            "bundled_target_resource_external_bin",
        ));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            candidates.push((parent.join(BACKEND_BASE_NAME), "bundle_macos_external_bin"));
            candidates.push((
                parent.join(&sidecar_name),
                "bundle_macos_target_external_bin",
            ));
            candidates.push((
                parent.join("../Resources/bin").join(BACKEND_BASE_NAME),
                "bundle_resources_bin_external_bin",
            ));
            candidates.push((
                parent.join("../Resources/bin").join(&sidecar_name),
                "bundle_resources_bin_target_external_bin",
            ));
            candidates.push((
                parent.join("../Resources").join(BACKEND_BASE_NAME),
                "bundle_resources_external_bin",
            ));
            candidates.push((
                parent.join("../Resources").join(&sidecar_name),
                "bundle_resources_target_external_bin",
            ));
        }
    }
    candidates.push((
        project_root
            .join("apps/desktop/src-tauri/bin")
            .join(BACKEND_ONEDIR_NAME)
            .join(BACKEND_BASE_NAME),
        "onedir_dev_known_path",
    ));
    candidates
}

fn locate_sidecar(
    app: &tauri::App,
    project_root: &Path,
) -> Result<(PathBuf, &'static str), String> {
    for (candidate, strategy) in sidecar_candidates(app, project_root) {
        if candidate.exists() {
            return Ok((candidate, strategy));
        }
    }
    Err(format!(
        "bundled sidecar not found; expected {BACKEND_BASE_NAME}-{BACKEND_TARGET}"
    ))
}

fn initialize_main_log(app: &tauri::App, state: &SidecarState) -> Result<PathBuf, String> {
    let app_data = app
        .path()
        .app_data_dir()
        .map_err(|error| format!("could not resolve app data dir: {error}"))?;
    let logs_dir = app_data.join("runtime").join("logs");
    std::fs::create_dir_all(&logs_dir)
        .map_err(|error| format!("could not create logs dir: {error}"))?;
    let mut guard = state.lock().map_err(|_| "sidecar state lock poisoned")?;
    guard.main_log_path = Some(logs_dir.join("desktop-main.log"));
    Ok(app_data)
}

fn start_sidecar(app: &tauri::App, state: &SidecarState) -> Result<(), String> {
    let app_data = initialize_main_log(app, state)?;
    log_event(state, "app_start", "packaged_tauri=true");
    log_event(state, "backend_health_check_start", HEALTH_URL);
    if health_ok() {
        log_event(
            state,
            "backend_health_check_result",
            "ok=true reused_existing=true",
        );
        return Ok(());
    }
    log_event(
        state,
        "backend_health_check_result",
        "ok=false reused_existing=false",
    );

    let runtime_dir = app_data.join("runtime");
    let playwright_dir = app_data.join("playwright-browsers");
    let logs_dir = runtime_dir.join("logs");
    std::fs::create_dir_all(&runtime_dir)
        .map_err(|error| format!("could not create runtime dir: {error}"))?;
    std::fs::create_dir_all(&logs_dir)
        .map_err(|error| format!("could not create logs dir: {error}"))?;
    std::fs::create_dir_all(&playwright_dir)
        .map_err(|error| format!("could not create playwright dir: {error}"))?;
    let stdout_path = logs_dir.join("desktop-sidecar-stdout.log");
    let stderr_path = logs_dir.join("desktop-sidecar-stderr.log");
    let stdout_log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&stdout_path)
        .map_err(|error| format!("could not open sidecar stdout log: {error}"))?;
    let stderr_log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&stderr_path)
        .map_err(|error| format!("could not open sidecar stderr log: {error}"))?;

    let project_root = std::env::var("LOCAL_AI_PROJECT_ROOT")
        .ok()
        .map(PathBuf::from)
        .unwrap_or_else(|| app_data.clone());
    let (sidecar, sidecar_strategy) = locate_sidecar(app, &project_root)?;
    let sidecar_args = vec![
        "--host".to_string(),
        "127.0.0.1".to_string(),
        "--port".to_string(),
        "8422".to_string(),
        "--project-root".to_string(),
        project_root.display().to_string(),
        "--runtime-dir".to_string(),
        runtime_dir.display().to_string(),
        "--playwright-browsers-path".to_string(),
        playwright_dir.display().to_string(),
    ];

    log_event(
        state,
        "sidecar_spawn_start",
        &format!("strategy={sidecar_strategy}"),
    );
    log_event(
        state,
        "sidecar_spawn_command",
        &format!("path={}", sidecar.display()),
    );
    log_event(state, "sidecar_args", &format!("{sidecar_args:?}"));
    log_event(
        state,
        "sidecar_env",
        &format!(
            "LOCAL_AI_INSTALLED_MODE=1 PYTHONUNBUFFERED=1 PROJECT_ROOT={} PLAYWRIGHT_BROWSERS_PATH={}",
            project_root.display(),
            playwright_dir.display()
        ),
    );
    log_event(
        state,
        "sidecar_working_dir",
        &format!("path={}", project_root.display()),
    );
    log_event(
        state,
        "sidecar_stdout_path",
        &format!("path={}", stdout_path.display()),
    );
    log_event(
        state,
        "sidecar_stderr_path",
        &format!("path={}", stderr_path.display()),
    );
    let child = Command::new(&sidecar)
        .args(&sidecar_args)
        .env("LOCAL_AI_INSTALLED_MODE", "1")
        .env("PYTHONUNBUFFERED", "1")
        .current_dir(&project_root)
        .stdout(Stdio::from(stdout_log))
        .stderr(Stdio::from(stderr_log))
        .spawn()
        .map_err(|error| format!("could not start sidecar: {error}"))?;
    let child_pid = child.id();

    {
        let mut guard = state.lock().map_err(|_| "sidecar state lock poisoned")?;
        guard.child = Some(child);
        guard.started_by_app = true;
    }
    log_event(
        state,
        "sidecar_spawn_pid",
        &format!("pid={child_pid} strategy={sidecar_strategy}"),
    );

    if wait_for_health(Duration::from_secs(180), state) {
        log_event(state, "sidecar_health_ready", HEALTH_URL);
        Ok(())
    } else {
        Err(format!(
            "sidecar did not become healthy before timeout; see {} and {}",
            stdout_path.display(),
            stderr_path.display()
        ))
    }
}

fn stop_sidecar(state: &SidecarState) {
    let Ok(mut guard) = state.lock() else {
        return;
    };
    if !guard.started_by_app {
        return;
    }
    if let Some(mut child) = guard.child.take() {
        let pid = child.id();
        drop(guard);
        log_event(state, "sidecar_shutdown_start", &format!("pid={pid}"));
        unsafe {
            libc::kill(pid as i32, libc::SIGTERM);
        }
        let deadline = Instant::now() + Duration::from_secs(5);
        while Instant::now() < deadline {
            match child.try_wait() {
                Ok(Some(_)) => {
                    log_event(
                        state,
                        "sidecar_shutdown_done",
                        &format!("pid={pid} graceful=true"),
                    );
                    return;
                }
                Ok(None) => thread::sleep(Duration::from_millis(100)),
                Err(_) => break,
            }
        }
        let _ = child.kill();
        let _ = child.wait();
        log_event(
            state,
            "sidecar_shutdown_done",
            &format!("pid={pid} graceful=false"),
        );
    }
}

fn main() {
    let sidecar_state: SidecarState = Arc::new(Mutex::new(SidecarLifecycle::default()));
    let setup_state = sidecar_state.clone();
    let run_state = sidecar_state.clone();

    let app = tauri::Builder::default()
        .setup(move |app| {
            if let Err(error) = start_sidecar(app, &setup_state) {
                eprintln!("[desktop] sidecar startup failed: {error}");
                log_event(
                    &setup_state,
                    "sidecar_health_ready",
                    &format!("ok=false error={error}"),
                );
            }
            if wait_for_health(Duration::from_secs(3), &setup_state) {
                if app.get_webview_window("main").is_some() {
                    log_event(&setup_state, "webview_created", "label=main");
                    log_event(
                        &setup_state,
                        "webview_load_start",
                        "source=tauri_frontend_dist api=http://127.0.0.1:8422",
                    );
                }
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Local AI Orchestrator desktop shell");

    app.run(move |_app_handle, event| {
        if matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. }) {
            log_event(&run_state, "app_close", "normal_exit=true");
            stop_sidecar(&run_state);
        }
    });
}
