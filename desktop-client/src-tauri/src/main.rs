use std::env;

use tauri::{WebviewUrl, WebviewWindowBuilder};

fn env_or(name: &str, fallback: &str) -> String {
    env::var(name).unwrap_or_else(|_| fallback.to_string())
}

fn launch_path() -> String {
    let number = env::var("FEACHAT_AUTO_LOGIN_NUMBER").unwrap_or_default();
    if number.is_empty() {
        return "index.html".to_string();
    }

    let password = env_or("FEACHAT_AUTO_LOGIN_PASSWORD", "secret1");
    let nickname = env_or("FEACHAT_AUTO_LOGIN_NICKNAME", &number);
    let email = env_or("FEACHAT_AUTO_LOGIN_EMAIL", &format!("{number}@example.com"));

    format!(
        "index.html?autoLogin=1&number={number}&password={password}&nickname={nickname}&email={email}"
    )
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let label = env_or("FEACHAT_WINDOW_LABEL", "main");
            let title = env::var("FEACHAT_AUTO_LOGIN_NUMBER")
                .map(|number| format!("FeaChat - {number}"))
                .unwrap_or_else(|_| "FeaChat".to_string());

            let window = WebviewWindowBuilder::new(app, label, WebviewUrl::App(launch_path().into()))
                .title(title)
                .inner_size(920.0, 660.0)
                .min_inner_size(760.0, 520.0)
                .decorations(false)
                .transparent(true)
                .shadow(true)
                .resizable(true);

            window.build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run FeaChat");
}
