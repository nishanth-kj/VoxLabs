use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

#[cfg(windows)]
mod windows_job;

/// Holds the handle to the spawned VoxLabs API sidecar so it can be killed on exit.
struct ApiProcess(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  let app = tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .manage(ApiProcess(Mutex::new(None)))
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
        // In dev, the API is already started separately (see package.json's
        // `dev:api` / `dev:desktop` scripts) - nothing to spawn here.
      } else {
        // In a packaged build there is no separate process starting the API,
        // so launch the bundled sidecar ourselves.
        let sidecar = app.shell().sidecar("voxlabs-api")?;
        let (_rx, child) = sidecar
          .spawn()
          .expect("failed to start the VoxLabs API sidecar");

        // Belt-and-braces: also tie the sidecar's lifetime to ours at the OS
        // level, so it's killed even if we don't get to run the
        // `ExitRequested` handler below (crash, "End Task", `taskkill /F`).
        #[cfg(windows)]
        if let Err(e) = windows_job::kill_with_parent(child.pid()) {
          log::warn!("failed to bind sidecar lifetime to the main process: {e}");
        }

        app.state::<ApiProcess>().0.lock().unwrap().replace(child);
      }
      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application");

  app.run(|app_handle, event| {
    if let tauri::RunEvent::ExitRequested { .. } = event {
      if let Some(child) = app_handle.state::<ApiProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
      }
    }
  });
}
