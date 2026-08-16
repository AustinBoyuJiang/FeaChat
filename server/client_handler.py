import json
import math
import os
import random
import re
import string
import threading
import time
from email.mime.text import MIMEText

try:
    from . import database
    from . import email_service
    from .config import EMAIL_ACCOUNT
    from .security import hash_password, verify_password
except ImportError:
    import database
    import email_service
    from config import EMAIL_ACCOUNT
    from security import hash_password, verify_password


class ClientHandler:
    USER_INFO_FIELDS = {"avatar", "background", "nickname", "birth", "gender", "motto"}
    BASE_DIR = os.path.dirname(__file__)

    def __init__(self, client, ip_address, server_ref):
        self.client = client
        self.ip_address = ip_address
        self.server = server_ref
        self.number = None
        self.hostname = ""
        self.mac_address = ""
        self.login_code = None
        self.register_code = None
        self.login_code_send_time = 0
        self.register_code_send_time = 0
        self.handlers = {
            "connect": self.connect,
            "login": self.login,
            "getUserInfo": self.get_user_info,
            "modifyUserInfo": self.modify_user_info,
            "getLoginDevices": self.get_login_devices,
            "register": self.register,
            "sendRegisterCode": self.send_register_code,
            "uploadFile": self.upload_file,
            "downloadFile": self.download_file,
            "getFileInfo": self.get_file_info,
            "sendMessage": self.send_message,
            "getMessages": self.get_messages,
            "searchUsers": self.search_users,
            "addFriend": self.add_friend,
            "getFriends": self.get_friends,
            "getFriendRequests": self.get_friend_requests,
            "acceptFriendRequest": self.accept_friend_request,
            "rejectFriendRequest": self.reject_friend_request,
            "deleteFriend": self.delete_friend,
        }
        threading.Thread(target=self.listen, daemon=True).start()

    # ------------------------------------------------------------------ core
    def _recv_all(self):
        header = b""
        while len(header) < 4:
            chunk = self.client.recv(4 - len(header))
            if not chunk:
                raise ConnectionError("Connection closed")
            header += chunk
        length = int.from_bytes(header, "big")
        data = b""
        while len(data) < length:
            chunk = self.client.recv(min(65536, length - len(data)))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data.decode("utf-8")

    def _send_json(self, payload):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.client.sendall(len(encoded).to_bytes(4, "big") + encoded)

    def listen(self):
        while True:
            try:
                raw = self._recv_all()
                request = json.loads(raw)
                action = request.get("action")
                payload = request.get("payload", [])
                print(f"[{self.ip_address}] -> {action}")

                handler = self.handlers.get(action)
                if handler is None:
                    self._send_json({"ok": False, "data": None, "error": "Unknown action"})
                    continue

                try:
                    data = handler(payload)
                    self._send_json({"ok": True, "data": data, "error": None})
                except ValueError as ex:
                    self._send_json({"ok": False, "data": None, "error": str(ex)})
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    self._send_json({"ok": False, "data": None, "error": str(ex)})
            except Exception as ex:
                print(f"[{self.ip_address}] connection error: {ex}")
                self.disconnect()
                break

    def disconnect(self):
        print(f"[{self.ip_address}] disconnected")
        self.server.clients.pop(self.ip_address, None)
        self.client.close()

    # ------------------------------------------------------------------ helpers
    def db_query(self, sql, *values):
        return database.query(self.server.db, sql, *values)

    def create_code(self, length):
        pool = string.ascii_letters + string.digits * 6
        return "".join(random.sample(pool, length))

    def validate_email(self, email):
        return bool(re.compile(r"^.+@.+").match(email))

    def require_login(self):
        if not self.number:
            raise ValueError("Not logged in")

    def message_tuple(self, row):
        return (
            str(row["id"]),
            row["sender"],
            row["receiver"],
            row["time"],
            row["type"],
            row["message"],
        )

    # ------------------------------------------------------------------ handlers
    def connect(self, payload):
        self.hostname, self.mac_address = payload
        return "connected"

    def login(self, payload):
        number, password = payload
        if not number:
            raise ValueError("The number can't be empty")
        if not password:
            raise ValueError("The password can't be empty")

        rows = self.db_query("SELECT number, password_hash FROM users WHERE number = ?;", number)
        if not rows or not verify_password(password, rows[0]["password_hash"]):
            raise ValueError("The number or password is wrong")
        if any(c.number == number for c in self.server.clients.values() if c is not self):
            raise ValueError("Account login elsewhere")

        self.number = number
        return {
            "message": "succeeded",
            "messages": self.get_messages([]),
        }

    def get_user_info(self, payload):
        number = payload[0]
        rows = self.db_query(
            """
            SELECT nickname, avatar, background, birth, gender, motto
            FROM users
            WHERE number = ?;
            """,
            number,
        )
        if not rows:
            raise ValueError("Account is not registered")
        return tuple(rows[0])

    def modify_user_info(self, payload):
        number, field, value = payload
        if field not in self.USER_INFO_FIELDS:
            raise ValueError("Unsupported user info field")
        if self.number is not None and number != self.number:
            raise ValueError("Cannot modify another account")
        self.db_query(
            f"UPDATE users SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE number = ?;",
            value,
            number,
        )
        return "updated"

    def get_login_devices(self, payload):
        self.require_login()
        number = payload[0]
        if number != self.number:
            raise ValueError("Cannot read another account")
        rows = self.db_query("SELECT devices FROM users WHERE number = ?;", number)
        return rows[0]["devices"] if rows else "{}"

    def register(self, payload):
        number, password, email, code, mac_address = payload
        if len(number) < 6:
            raise ValueError("The number length is at least 6")
        if len(password) < 6:
            raise ValueError("The password length is at least 6")
        if not email:
            raise ValueError("The email can't be empty")
        if code is None or code != self.register_code:
            raise ValueError("The verification code is wrong")
        if time.time() - self.register_code_send_time > 600:
            raise ValueError("The verification code has expired")

        if self.db_query("SELECT number FROM users WHERE number = ?;", number):
            raise ValueError("The number has already been registered")
        if self.db_query("SELECT number FROM users WHERE email = ?;", email):
            raise ValueError("The email has already been bound")

        devices = json.dumps({mac_address: self.hostname}, ensure_ascii=False)
        self.db_query(
            """
            INSERT INTO users(number, password_hash, email, devices)
            VALUES (?, ?, ?, ?);
            """,
            number,
            hash_password(password),
            email,
            devices,
        )
        return "Registered successfully"

    def send_register_code(self, payload):
        email = payload[0]
        spacing = 60 - time.time() + self.register_code_send_time
        if spacing > 0:
            raise ValueError(f"You need to wait {math.ceil(spacing)}s")
        if not email:
            raise ValueError("The email can't be empty")
        if not self.validate_email(email):
            raise ValueError("The email format is incorrect")

        self.register_code_send_time = time.time()
        self.register_code = self.create_code(6)
        template_path = os.path.join(self.BASE_DIR, "SMTP HTML", "Register Code.html")
        html = open(template_path, "rb").read().decode("utf-8") % self.register_code
        content = MIMEText(html, "html", "utf-8")

        if not EMAIL_ACCOUNT:
            return f"Sent successfully (development code: {self.register_code})"

        def send_async():
            try:
                email_service.send_email(email, content, "Register Code")
                print(f"[email] Register code sent to {email}")
            except Exception as ex:
                print(f"[email] Failed to send to {email}: {ex}")

        threading.Thread(target=send_async, daemon=True).start()
        return "Sent successfully"

    def upload_file(self, payload):
        size, name, extension, data = payload
        cursor = self.server.db.cursor()
        cursor.execute(
            """
            INSERT INTO files(size, name, extension, data)
            VALUES (?, ?, ?, ?);
            """,
            (size, name, extension, data),
        )
        self.server.db.commit()
        return cursor.lastrowid

    def download_file(self, payload):
        fid = payload[0]
        rows = self.db_query("SELECT data FROM files WHERE id = ?;", fid)
        if not rows:
            raise ValueError("File not found")
        return rows[0]["data"]

    def get_file_info(self, payload):
        fid = payload[0]
        rows = self.db_query("SELECT size, name, extension FROM files WHERE id = ?;", fid)
        if not rows:
            raise ValueError("File not found")
        return tuple(rows[0])

    def search_users(self, payload):
        self.require_login()
        keyword = payload[0].strip() if payload else ""
        if not keyword:
            return []
        rows = self.db_query(
            """
            SELECT number, nickname, avatar, motto
            FROM users
            WHERE number LIKE ? OR nickname LIKE ?
            ORDER BY number
            LIMIT 20;
            """,
            f"%{keyword}%",
            f"%{keyword}%",
        )
        return [
            (row["number"], row["nickname"], row["avatar"], row["motto"])
            for row in rows
            if row["number"] != self.number
        ]

    def add_friend(self, payload):
        self.require_login()
        friend = payload[0]
        if friend == self.number:
            raise ValueError("You cannot add yourself")
        if not self.db_query("SELECT number FROM users WHERE number = ?;", friend):
            raise ValueError("Account is not registered")
        if self.db_query(
            "SELECT 1 FROM friendships WHERE owner = ? AND friend = ?;",
            self.number,
            friend,
        ):
            return "Already friends"

        reciprocal = self.db_query(
            """
            SELECT id FROM friend_requests
            WHERE requester = ? AND receiver = ? AND status = 'pending';
            """,
            friend,
            self.number,
        )
        if reciprocal:
            return self.accept_friend_request([friend])

        existing = self.db_query(
            """
            SELECT status FROM friend_requests
            WHERE requester = ? AND receiver = ?;
            """,
            self.number,
            friend,
        )
        if existing and existing[0]["status"] == "pending":
            return "Friend request already sent"

        self.db_query(
            """
            INSERT INTO friend_requests(requester, receiver, status)
            VALUES (?, ?, 'pending')
            ON CONFLICT(requester, receiver)
            DO UPDATE SET status = 'pending', updated_at = CURRENT_TIMESTAMP;
            """,
            self.number,
            friend,
        )
        return "Friend request sent"

    def get_friends(self, payload):
        self.require_login()
        rows = self.db_query(
            """
            SELECT u.number, u.nickname, u.avatar, u.motto
            FROM friendships f
            JOIN users u ON u.number = f.friend
            WHERE f.owner = ?
            ORDER BY u.nickname, u.number;
            """,
            self.number,
        )
        return [(row["number"], row["nickname"], row["avatar"], row["motto"]) for row in rows]

    def get_friend_requests(self, payload):
        self.require_login()
        rows = self.db_query(
            """
            SELECT r.requester, u.nickname, u.avatar, u.motto, r.created_at
            FROM friend_requests r
            JOIN users u ON u.number = r.requester
            WHERE r.receiver = ? AND r.status = 'pending'
            ORDER BY r.created_at DESC;
            """,
            self.number,
        )
        return [
            (row["requester"], row["nickname"], row["avatar"], row["motto"], row["created_at"])
            for row in rows
        ]

    def accept_friend_request(self, payload):
        self.require_login()
        requester = payload[0]
        if not self.db_query(
            """
            SELECT id FROM friend_requests
            WHERE requester = ? AND receiver = ? AND status = 'pending';
            """,
            requester,
            self.number,
        ):
            raise ValueError("Friend request not found")
        self.db_query(
            """
            UPDATE friend_requests
            SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
            WHERE requester = ? AND receiver = ?;
            """,
            requester,
            self.number,
        )
        self.db_query(
            "INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?);",
            self.number,
            requester,
        )
        self.db_query(
            "INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?);",
            requester,
            self.number,
        )
        return "Friend request accepted"

    def reject_friend_request(self, payload):
        self.require_login()
        requester = payload[0]
        self.db_query(
            """
            UPDATE friend_requests
            SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE requester = ? AND receiver = ? AND status = 'pending';
            """,
            requester,
            self.number,
        )
        return "Friend request rejected"

    def delete_friend(self, payload):
        self.require_login()
        friend = payload[0]
        self.db_query(
            "DELETE FROM friendships WHERE (owner = ? AND friend = ?) OR (owner = ? AND friend = ?);",
            self.number,
            friend,
            friend,
            self.number,
        )
        return "Friend deleted"

    def send_message(self, payload):
        self.require_login()
        receiver, message_type, message = payload
        if message_type not in {"text", "file", "link", "emoji"}:
            raise ValueError("Unsupported message type")
        if not self.db_query("SELECT number FROM users WHERE number = ?;", receiver):
            raise ValueError("Receiver is not registered")

        cursor = self.server.db.cursor()
        cursor.execute(
            """
            INSERT INTO messages(sender, receiver, type, message)
            VALUES (?, ?, ?, ?);
            """,
            (self.number, receiver, message_type, message),
        )
        self.server.db.commit()
        row = self.db_query("SELECT * FROM messages WHERE id = ?;", cursor.lastrowid)[0]
        msg = self.message_tuple(row)

        for client in self.server.clients.values():
            if client is not self and client.number == receiver:
                try:
                    client._send_json({"ok": True, "data": {"event": "message", "message": msg}, "error": None})
                except Exception:
                    pass
        return msg

    def get_messages(self, payload):
        self.require_login()
        peer = payload[0] if payload else None
        limit = int(payload[1]) if len(payload) > 1 else 200
        limit = max(1, min(limit, 500))

        if peer:
            rows = self.db_query(
                """
                SELECT * FROM messages
                WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                ORDER BY time ASC, id ASC
                LIMIT ?;
                """,
                self.number,
                peer,
                peer,
                self.number,
                limit,
            )
        else:
            rows = self.db_query(
                """
                SELECT * FROM messages
                WHERE sender = ? OR receiver = ?
                ORDER BY time ASC, id ASC
                LIMIT ?;
                """,
                self.number,
                self.number,
                limit,
            )
        return [self.message_tuple(row) for row in rows]
