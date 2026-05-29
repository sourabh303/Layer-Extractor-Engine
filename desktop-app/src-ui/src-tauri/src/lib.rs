use std::sync::Mutex;
use rand::{Rng, thread_rng};
use rand::distributions::Alphanumeric;
use tauri::{Manager, State};

struct IpcSecret(Mutex<String>);

#[tauri::command]
fn get_ipc_secret(secret: State<'_, IpcSecret>) -> String {
    secret.0.lock().unwrap().clone()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let random_token: String = thread_rng()
        .sample_iter(&Alphanumeric)
        .take(64)
        .map(char::from)
        .collect();

    tauri::Builder::default()
        .manage(IpcSecret(Mutex::new(random_token)))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![get_ipc_secret])
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
