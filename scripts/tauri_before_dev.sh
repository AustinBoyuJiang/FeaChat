#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if lsof -iTCP:1420 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Vite is already listening on http://127.0.0.1:1420; reusing it for Tauri."
  exit 0
fi

cd "$ROOT/desktop-client"
exec npm run dev

