#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
CONDA_SH="$HOME/miniforge3/etc/profile.d/conda.sh"

mkdir -p "$LOG_DIR"

if [[ -f "$CONDA_SH" ]]; then
  # shellcheck disable=SC1090
  source "$CONDA_SH"
fi

echo "[FeaChat] Preparing local test accounts..."
conda run -n feachat-server python -c "
import base64, os
from server import database
from server.config import BASE_DIR
from server.security import hash_password

conn = database.get_connection()
database.ensure_schema(conn)

def file_id(path):
    name, ext = os.path.splitext(os.path.basename(path))
    row = conn.execute('SELECT id FROM files WHERE name = ? AND extension = ? LIMIT 1;', (name, ext)).fetchone()
    if row:
        return row['id']
    data = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO files(size, name, extension, data) VALUES (?, ?, ?, ?);',
        (os.path.getsize(path), name, ext, data),
    )
    conn.commit()
    return cur.lastrowid

avatar_id = file_id(os.path.join(BASE_DIR, 'pic', 'default avatar.png'))
bg_id = file_id(os.path.join(BASE_DIR, 'pic', 'default background picture.png'))

for number, nickname, email, gender, motto in [
    ('alice1', 'Alice', 'alice1@example.com', 'Girl', 'Hello, I am Alice.'),
    ('bob001', 'Bob', 'bob001@example.com', 'Boy', 'Hello, I am Bob.'),
]:
    conn.execute(
        '''
        INSERT INTO users(number, password_hash, email, devices, avatar, background, nickname, birth, gender, motto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(number) DO UPDATE SET
            password_hash = excluded.password_hash,
            email = excluded.email,
            avatar = excluded.avatar,
            background = excluded.background,
            nickname = excluded.nickname,
            gender = excluded.gender,
            motto = excluded.motto,
            updated_at = CURRENT_TIMESTAMP;
        ''',
        (number, hash_password('secret1'), email, '{}', avatar_id, bg_id, nickname, '2000-01-01', gender, motto),
    )

conn.execute(\"DELETE FROM friendships WHERE owner IN ('alice1', 'bob001') OR friend IN ('alice1', 'bob001');\")
conn.execute(\"DELETE FROM friend_requests WHERE requester IN ('alice1', 'bob001') OR receiver IN ('alice1', 'bob001');\")
conn.commit()
conn.close()
print('Ready: alice1 / secret1, bob001 / secret1')
"

if conda run -n feachat-server python -c "import socket; s=socket.create_connection(('127.0.0.1', 8888), timeout=1); s.close()" >/dev/null 2>&1; then
  echo "[FeaChat] Server already listening on 127.0.0.1:8888"
else
  echo "[FeaChat] Starting server..."
  (
    cd "$ROOT_DIR"
    conda run -n feachat-server python -m server
  ) >"$LOG_DIR/server.log" 2>&1 &
  sleep 1
fi

echo "[FeaChat] Starting Alice and Bob clients..."
(
  cd "$ROOT_DIR"
  FEACHAT_DEV_MODE=0 \
  FEACHAT_AUTO_LOGIN_NUMBER=alice1 \
  FEACHAT_AUTO_LOGIN_PASSWORD=secret1 \
  FEACHAT_WINDOW_OFFSET_X=-120 \
  FEACHAT_WINDOW_OFFSET_Y=0 \
  conda run -n feachat-client python -m client
) >"$LOG_DIR/alice.log" 2>&1 &

(
  cd "$ROOT_DIR"
  FEACHAT_DEV_MODE=0 \
  FEACHAT_AUTO_LOGIN_NUMBER=bob001 \
  FEACHAT_AUTO_LOGIN_PASSWORD=secret1 \
  FEACHAT_WINDOW_OFFSET_X=120 \
  FEACHAT_WINDOW_OFFSET_Y=30 \
  conda run -n feachat-client python -m client
) >"$LOG_DIR/bob.log" 2>&1 &

echo "[FeaChat] Done. Logs are in $LOG_DIR"
