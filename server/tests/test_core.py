import os
import sqlite3
import tempfile
import unittest

from server import database
from server.client_handler import ClientHandler


class FakeServer:
    def __init__(self, conn):
        self.db = conn
        self.clients = {}


def make_handler(conn):
    handler = ClientHandler.__new__(ClientHandler)
    handler.client = None
    handler.ip_address = ("test", 0)
    handler.server = FakeServer(conn)
    handler.number = None
    handler.hostname = "test-host"
    handler.mac_address = "00:00:00:00:00:00"
    handler.login_code = None
    handler.register_code = "ABC123"
    handler.login_code_send_time = 0
    handler.register_code_send_time = 9_999_999_999
    handler.handlers = {}
    return handler


class CoreFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "feachat.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        database.init_db(self.conn)
        self.handler = make_handler(self.conn)

    def tearDown(self):
        self.conn.close()
        self.tmpdir.cleanup()

    def register_user(self, number):
        return self.handler.register(
            [number, "secret1", f"{number}@example.com", "ABC123", "mac"]
        )

    def test_register_login_profile_and_text_message(self):
        self.assertEqual(self.register_user("alice1"), "Registered successfully")
        self.assertEqual(self.register_user("bob001"), "Registered successfully")

        self.assertEqual(self.handler.login(["alice1", "secret1"])["message"], "succeeded")
        self.assertEqual(
            self.handler.modify_user_info(["alice1", "nickname", "Alice"]),
            "updated",
        )
        self.assertEqual(self.handler.get_user_info(["alice1"])[0], "Alice")

        self.assertEqual(self.handler.add_friend(["bob001"]), "Friend request sent")
        self.assertEqual(self.handler.get_friends([]), [])

        bob_handler = make_handler(self.conn)
        self.assertEqual(bob_handler.login(["bob001", "secret1"])["message"], "succeeded")
        requests = bob_handler.get_friend_requests([])
        self.assertEqual(requests[0][0], "alice1")
        self.assertEqual(
            bob_handler.accept_friend_request(["alice1"]),
            "Friend request accepted",
        )

        friends = self.handler.get_friends([])
        self.assertEqual(friends[0][0], "bob001")

        message = self.handler.send_message(["bob001", "text", "Hello Bob"])
        self.assertEqual(message[1], "alice1")
        self.assertEqual(message[2], "bob001")
        self.assertEqual(message[4], "text")
        self.assertEqual(message[5], "Hello Bob")

        messages = self.handler.get_messages(["bob001", 50])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][5], "Hello Bob")

        self.assertEqual(self.handler.delete_friend(["bob001"]), "Friend deleted")
        self.assertEqual(self.handler.get_friends([]), [])

    def test_login_rejects_wrong_password(self):
        self.register_user("alice1")
        with self.assertRaises(ValueError):
            self.handler.login(["alice1", "wrong"])


if __name__ == "__main__":
    unittest.main()
