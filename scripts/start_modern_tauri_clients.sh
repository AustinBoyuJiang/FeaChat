#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/miniforge3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
fi

wait_for_port() {
  local port="$1"
  local name="$2"
  for _ in {1..40}; do
    if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "$name did not start on port $port" >&2
  return 1
}

stop_screen() {
  local name="$1"
  screen -S "$name" -X quit >/dev/null 2>&1 || true
}

stop_port() {
  local port="$1"
  local name="$2"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Stopping existing $name listener on port $port"
    kill $pids
    for _ in {1..20}; do
      if ! lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        return 0
      fi
      sleep 0.2
    done
    echo "$name on port $port did not stop cleanly" >&2
    return 1
  fi
}

stop_tauri_clients() {
  local pattern="$ROOT/desktop-client/src-tauri/target/debug/feachat"
  local pids
  pids="$(pgrep -f "$pattern" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Stopping existing FeaChat Tauri windows"
    kill $pids
    sleep 0.5
  fi
}

cd "$ROOT"
stop_screen feachat-server
stop_screen feachat-vite
stop_screen feachat-alice
stop_screen feachat-bob
stop_tauri_clients
conda run -n feachat-server python scripts/seed_modern_dev.py

stop_port 8000 "FastAPI server"
screen -dmS feachat-server bash -lc "cd '$ROOT' && conda run -n feachat-server python -m server > '$LOG_DIR/modern-server.log' 2>&1"
echo "Started FastAPI server on http://127.0.0.1:8000"
wait_for_port 8000 "FastAPI server"

cd "$ROOT/desktop-client"
stop_port 1420 "Vite client"
rm -rf "$ROOT/desktop-client/dist" "$ROOT/desktop-client/node_modules/.vite"
rm -rf "$ROOT/desktop-client/src-tauri/target/debug/bundle"
rm -f "$ROOT/desktop-client/src-tauri/target/debug/feachat"
rm -rf "$ROOT/desktop-client/src-tauri/target/debug/feachat.dSYM"
find "$ROOT/desktop-client/src-tauri/target/debug/deps" -maxdepth 1 -name 'feachat*' -delete 2>/dev/null || true
find "$ROOT/desktop-client/src-tauri/target/debug/incremental" -maxdepth 1 -name 'feachat*' -exec rm -rf {} + 2>/dev/null || true
screen -dmS feachat-vite bash -lc "cd '$ROOT/desktop-client' && npm run dev > '$LOG_DIR/modern-client.log' 2>&1"
echo "Started Vite client on http://127.0.0.1:1420"
wait_for_port 1420 "Vite client"

screen -dmS feachat-alice bash -lc "cd '$ROOT/desktop-client' && FEACHAT_WINDOW_LABEL=alice FEACHAT_AUTO_LOGIN_NUMBER=alice1 FEACHAT_AUTO_LOGIN_PASSWORD=secret1 FEACHAT_AUTO_LOGIN_NICKNAME=Alice FEACHAT_AUTO_LOGIN_EMAIL=alice1@example.com npm run tauri dev > '$LOG_DIR/tauri-alice.log' 2>&1"

sleep 2

screen -dmS feachat-bob bash -lc "cd '$ROOT/desktop-client' && FEACHAT_WINDOW_LABEL=bob FEACHAT_AUTO_LOGIN_NUMBER=bob001 FEACHAT_AUTO_LOGIN_PASSWORD=secret1 FEACHAT_AUTO_LOGIN_NICKNAME=Bob FEACHAT_AUTO_LOGIN_EMAIL=bob001@example.com npm run tauri dev > '$LOG_DIR/tauri-bob.log' 2>&1"

echo "Started two Tauri test clients:"
echo "  Alice: alice1 / secret1"
echo "  Bob:   bob001 / secret1"
echo "Logs:"
echo "  $LOG_DIR/modern-server.log"
echo "  $LOG_DIR/modern-client.log"
echo "  $LOG_DIR/tauri-alice.log"
echo "  $LOG_DIR/tauri-bob.log"
