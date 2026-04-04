import os
import sqlite3
from config import DB_PATH


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    """Drop and recreate all tables."""
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS messages;

        CREATE TABLE users (
            id INTEGER,
            number TEXT,
            password TEXT,
            email TEXT,
            devices TEXT,
            avatar INTEGER,
            background INTEGER,
            nickname TEXT,
            birth TEXT,
            gender TEXT,
            motto TEXT
        );

        CREATE TABLE files (
            id INTEGER,
            size INTEGER,
            name TEXT,
            extension TEXT,
            data LONGTEXT
        );

        CREATE TABLE messages (
            id INTEGER,
            sender INTEGER,
            receiver INTEGER,
            time TEXT,
            type TEXT,
            message TEXT
        );
    """)
    conn.commit()


def clear_db(conn):
    """Delete all rows from all tables."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM users;
        DELETE FROM files;
        DELETE FROM messages;
    """)
    conn.commit()


def query(conn, sql, *values):
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    return cursor.fetchall()
