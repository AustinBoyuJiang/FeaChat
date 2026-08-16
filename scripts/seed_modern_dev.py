import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.app.db import db
from server.app.services import generate_avatar_color
from server.security import hash_password


USERS = [
    ("alice1", "Alice", "alice1@example.com", "female"),
    ("bob001", "Bob", "bob001@example.com", "male"),
]
PASSWORD = "secret1"


def main():
    for number, nickname, email, gender in USERS:
        db.execute(
            """
            INSERT INTO users(number, password_hash, email, nickname, gender, motto, avatar_color)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(number)
            DO UPDATE SET
                password_hash = excluded.password_hash,
                email = excluded.email,
                nickname = excluded.nickname,
                gender = excluded.gender,
                motto = excluded.motto,
                avatar_color = COALESCE(NULLIF(users.avatar_color, ''), excluded.avatar_color)
            """,
            number,
            hash_password(PASSWORD),
            email,
            nickname,
            gender,
            "FeaChat modern dev account",
            generate_avatar_color(),
        )

    db.execute("INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?)", "alice1", "bob001")
    db.execute("INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?)", "bob001", "alice1")
    print("Seeded alice1/bob001 with password secret1")


if __name__ == "__main__":
    main()
