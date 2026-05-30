// Minimal Tauri shell. Backend is launched by beforeDevCommand in tauri.conf.json.
fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Local AI Orchestrator desktop shell");
}
