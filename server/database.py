import os
import sqlite3

try:
    from .config import DB_PATH
except ImportError:
    from config import DB_PATH


def get_connection():
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    ensure_schema(conn)
    return conn


def ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS friendships (
            owner TEXT NOT NULL,
            friend TEXT NOT NULL,
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
    """)
    conn.commit()


def init_db(conn):
    """Drop and recreate all tables."""
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS friend_requests;
        DROP TABLE IF EXISTS friendships;
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            devices TEXT NOT NULL DEFAULT '{}',
            avatar INTEGER,
            background INTEGER,
            nickname TEXT NOT NULL DEFAULT '',
            birth TEXT NOT NULL DEFAULT '',
            gender TEXT NOT NULL DEFAULT '',
            motto TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            size INTEGER NOT NULL,
            name TEXT NOT NULL,
            extension TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender) REFERENCES users(number),
            FOREIGN KEY(receiver) REFERENCES users(number)
        );

        CREATE INDEX idx_messages_pair_time
            ON messages(sender, receiver, time);

        CREATE TABLE friendships (
            owner TEXT NOT NULL,
            friend TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(owner, friend),
            FOREIGN KEY(owner) REFERENCES users(number),
            FOREIGN KEY(friend) REFERENCES users(number),
            CHECK(owner <> friend)
        );

        CREATE INDEX idx_friendships_friend
            ON friendships(friend);

        CREATE TABLE friend_requests (
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

        CREATE INDEX idx_friend_requests_receiver_status
            ON friend_requests(receiver, status);
    """)
    conn.commit()


def clear_db(conn):
    """Delete all rows from all tables."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM messages;
        DELETE FROM friend_requests;
        DELETE FROM friendships;
        DELETE FROM files;
        DELETE FROM users;
    """)
    conn.commit()


def query(conn, sql, *values):
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    return cursor.fetchall()
