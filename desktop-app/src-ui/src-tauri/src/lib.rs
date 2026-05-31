use rand::RngCore;
use base64::Engine;

struct IpcSecret(String);

#[tauri::command]
fn get_machine_id() -> Result<String, String> {
    machine_uid::get().map_err(|e| e.to_string())
}

#[tauri::command]
fn get_ipc_secret(state: tauri::State<IpcSecret>) -> String {
    state.0.clone()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Generate secure random string for IPC Token
    let mut rng = rand::rng();
    let mut bytes = [0u8; 32];
    rng.fill_bytes(&mut bytes);
    let secret = base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(&bytes);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(IpcSecret(secret))
        .invoke_handler(tauri::generate_handler![get_machine_id, get_ipc_secret])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
