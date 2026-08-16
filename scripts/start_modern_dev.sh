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

cd "$ROOT"
conda run -n feachat-server python scripts/seed_modern_dev.py

if ! lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  conda run -n feachat-server python -m server >"$LOG_DIR/modern-server.log" 2>&1 &
  echo "Started FastAPI server on http://127.0.0.1:8000"
else
  echo "FastAPI server already appears to be listening on port 8000"
fi

cd "$ROOT/desktop-client"
if ! lsof -iTCP:1420 -sTCP:LISTEN >/dev/null 2>&1; then
  npm run dev >"$LOG_DIR/modern-client.log" 2>&1 &
  echo "Started Vite client on http://127.0.0.1:1420"
else
  echo "Vite client already appears to be listening on port 1420"
fi

sleep 2

ALICE_URL="http://127.0.0.1:1420/?autoLogin=1&number=alice1&password=secret1"
BOB_URL="http://127.0.0.1:1420/?autoLogin=1&number=bob001&password=secret1"

if command -v open >/dev/null 2>&1; then
  open -na "Google Chrome" --args --user-data-dir="/tmp/feachat-modern-alice" "$ALICE_URL" >/dev/null 2>&1 || open "$ALICE_URL"
  open -na "Google Chrome" --args --user-data-dir="/tmp/feachat-modern-bob" "$BOB_URL" >/dev/null 2>&1 || open "$BOB_URL"
else
  echo "Alice: $ALICE_URL"
  echo "Bob:   $BOB_URL"
fi

echo "Logs:"
echo "  $LOG_DIR/modern-server.log"
echo "  $LOG_DIR/modern-client.log"

