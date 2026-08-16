import hashlib
import sqlite3
import threading
from pathlib import Path

from .config import settings


class Database:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.db_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.ensure_schema()

    def ensure_schema(self):
        with self.lock:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    avatar INTEGER,
                    avatar_file TEXT,
                    avatar_mime_type TEXT,
                    avatar_color TEXT NOT NULL DEFAULT '#0076f6',
                    background INTEGER,
                    nickname TEXT NOT NULL DEFAULT '',
                    gender TEXT NOT NULL DEFAULT 'unknown',
                    motto TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(sender) REFERENCES users(number),
                    FOREIGN KEY(receiver) REFERENCES users(number)
                );

                CREATE INDEX IF NOT EXISTS idx_messages_pair_time
                    ON messages(sender, receiver, time);

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    owner TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK(type IN ('direct', 'group')),
                    CHECK(status IN ('active', 'dissolved')),
                    FOREIGN KEY(owner) REFERENCES users(number)
                );

                CREATE TABLE IF NOT EXISTS conversation_members (
                    conversation_id TEXT NOT NULL,
                    user_number TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    alias TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    left_at TEXT,
                    left_message_id INTEGER,
                    PRIMARY KEY(conversation_id, user_number),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_number) REFERENCES users(number),
                    CHECK(role IN ('owner', 'member')),
                    CHECK(status IN ('active', 'left'))
                );

                CREATE INDEX IF NOT EXISTS idx_conversation_members_user
                    ON conversation_members(user_number, status);

                CREATE TABLE IF NOT EXISTS group_invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    inviter TEXT NOT NULL,
                    invitee TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY(inviter) REFERENCES users(number),
                    FOREIGN KEY(invitee) REFERENCES users(number),
                    CHECK(inviter <> invitee),
                    CHECK(status IN ('pending', 'accepted', 'rejected'))
                );

                CREATE INDEX IF NOT EXISTS idx_group_invites_invitee_status
                    ON group_invites(invitee, status);

                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL UNIQUE,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_attachments_message
                    ON attachments(message_id);

                CREATE TABLE IF NOT EXISTS friendships (
                    owner TEXT NOT NULL,
                    friend TEXT NOT NULL,
                    alias TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(owner, friend),
                    FOREIGN KEY(owner) REFERENCES users(number),
                    FOREIGN KEY(friend) REFERENCES users(number),
                    CHECK(owner <> friend)
                );

                CREATE INDEX IF NOT EXISTS idx_friendships_friend
                    ON friendships(friend);

                CREATE TABLE IF NOT EXISTS friend_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requester TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(requester, receiver),
                    FOREIGN KEY(requester) REFERENCES users(number),
                    FOREIGN KEY(receiver) REFERENCES users(number),
                    CHECK(requester <> receiver),
                    CHECK(status IN ('pending', 'accepted', 'rejected'))
                );

                CREATE INDEX IF NOT EXISTS idx_friend_requests_receiver_status
                    ON friend_requests(receiver, status);

                CREATE TABLE IF NOT EXISTS moment_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT NOT NULL,
                    body TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(author) REFERENCES users(number)
                );

                CREATE INDEX IF NOT EXISTS idx_moment_posts_author_time
                    ON moment_posts(author, created_at);

                CREATE TABLE IF NOT EXISTS moment_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(post_id) REFERENCES moment_posts(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_moment_images_post
                    ON moment_images(post_id, position);

                CREATE TABLE IF NOT EXISTS moment_likes (
                    post_id INTEGER NOT NULL,
                    user_number TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(post_id, user_number),
                    FOREIGN KEY(post_id) REFERENCES moment_posts(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_number) REFERENCES users(number)
                );

                CREATE TABLE IF NOT EXISTS moment_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    author TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(post_id) REFERENCES moment_posts(id) ON DELETE CASCADE,
                    FOREIGN KEY(author) REFERENCES users(number)
                );

                CREATE INDEX IF NOT EXISTS idx_moment_comments_post
                    ON moment_comments(post_id, created_at);

                CREATE TABLE IF NOT EXISTS moment_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    post_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    comment_id INTEGER,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(owner) REFERENCES users(number),
                    FOREIGN KEY(actor) REFERENCES users(number),
                    FOREIGN KEY(post_id) REFERENCES moment_posts(id) ON DELETE CASCADE,
                    FOREIGN KEY(comment_id) REFERENCES moment_comments(id) ON DELETE CASCADE,
                    CHECK(type IN ('like', 'comment'))
                );

                CREATE INDEX IF NOT EXISTS idx_moment_notifications_owner_read
                    ON moment_notifications(owner, is_read, created_at);
                """
            )
            self._ensure_column("users", "gender", "TEXT NOT NULL DEFAULT 'unknown'")
            self._ensure_column("users", "avatar_file", "TEXT")
            self._ensure_column("users", "avatar_mime_type", "TEXT")
            self._ensure_column("users", "avatar_color", "TEXT NOT NULL DEFAULT '#0076f6'")
            self._backfill_avatar_colors()
            self._remove_group_invites_unique_constraint()
            self._ensure_column("messages", "conversation_id", "TEXT")
            self._ensure_column("conversations", "status", "TEXT NOT NULL DEFAULT 'active'")
            self._ensure_column("conversation_members", "left_at", "TEXT")
            self._ensure_column("conversation_members", "left_message_id", "INTEGER")
            self._ensure_column("friendships", "alias", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("friendships", "tags", "TEXT NOT NULL DEFAULT '[]'")
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, time)"
            )
            self.conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str):
        columns = {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _backfill_avatar_colors(self):
        rows = self.conn.execute(
            """
            SELECT number
            FROM users
            WHERE avatar IS NULL AND (avatar_color IS NULL OR avatar_color = '' OR avatar_color = '#0076f6')
            """
        ).fetchall()
        for row in rows:
            digest = hashlib.sha256(row["number"].encode("utf-8")).digest()
            hue = int.from_bytes(digest[:2], "big") % 360
            self.conn.execute(
                "UPDATE users SET avatar_color = ? WHERE number = ?",
                (f"hsl({hue} 72% 46%)", row["number"]),
            )

    def _remove_group_invites_unique_constraint(self):
        row = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'group_invites'"
        ).fetchone()
        if row is None or "UNIQUE(conversation_id, invitee)" not in (row["sql"] or ""):
            return
        self.conn.executescript(
            """
            CREATE TABLE group_invites_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                inviter TEXT NOT NULL,
                invitee TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY(inviter) REFERENCES users(number),
                FOREIGN KEY(invitee) REFERENCES users(number),
                CHECK(inviter <> invitee),
                CHECK(status IN ('pending', 'accepted', 'rejected'))
            );

            INSERT INTO group_invites_new(id, conversation_id, inviter, invitee, status, created_at, updated_at)
            SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
            FROM group_invites;

            DROP TABLE group_invites;
            ALTER TABLE group_invites_new RENAME TO group_invites;
            CREATE INDEX IF NOT EXISTS idx_group_invites_invitee_status
                ON group_invites(invitee, status);
            """
        )

    def fetchone(self, sql: str, *params):
        with self.lock:
            return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, *params):
        with self.lock:
            return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, *params):
        with self.lock:
            cursor = self.conn.execute(sql, params)
            self.conn.commit()
            return cursor

    def executescript(self, sql: str):
        with self.lock:
            self.conn.executescript(sql)
            self.conn.commit()


db = Database()
