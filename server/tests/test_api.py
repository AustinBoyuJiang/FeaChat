import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from server.app.db import Database
from server.app import main as app_main
from server.app.services import sessions


class ApiFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.tmpdir.name) / "feachat.db")
        self.previous_db = app_main.db
        self.previous_settings = app_main.settings
        app_main.db = self.database
        app_main.settings = replace(app_main.settings, upload_dir=Path(self.tmpdir.name) / "uploads")
        sessions.clear()
        self.client = TestClient(app_main.app)

    def tearDown(self):
        self.client.close()
        app_main.db = self.previous_db
        app_main.settings = self.previous_settings
        self.database.conn.close()
        self.tmpdir.cleanup()

    def register(self, number, nickname):
        response = self.client.post(
            "/api/auth/register",
            json={
                "number": number,
                "password": "secret1",
                "email": f"{number}@example.com",
                "nickname": nickname,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

    def login(self, number):
        response = self.client.post(
            "/api/auth/login",
            json={"number": number, "password": "secret1"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["token"]

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_friend_and_message_flow(self):
        self.register("alice1", "Alice")
        self.register("bob001", "Bob")
        alice = self.login("alice1")
        bob = self.login("bob001")

        response = self.client.get("/api/users/search?q=bob", headers=self.auth(alice))
        self.assertEqual(response.json()["users"][0]["number"], "bob001")

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(alice),
            json={"receiver": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get("/api/friends/requests", headers=self.auth(bob))
        self.assertEqual(response.json()["requests"][0]["number"], "alice1")

        response = self.client.get("/api/friends/requests/history", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["requests"][0]["direction"], "outgoing")
        self.assertEqual(response.json()["requests"][0]["status"], "pending")

        response = self.client.post("/api/friends/requests/alice1/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get("/api/friends", headers=self.auth(alice))
        self.assertEqual(response.json()["friends"][0]["number"], "bob001")

        response = self.client.get("/api/friends/requests/history", headers=self.auth(bob))
        self.assertEqual(response.json()["requests"][0]["direction"], "incoming")
        self.assertEqual(response.json()["requests"][0]["status"], "accepted")

        response = self.client.patch(
            "/api/friends/bob001",
            headers=self.auth(alice),
            json={"alias": "Bobby", "tags": ["work", "Work", "  friend  "]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["friend"]["alias"], "Bobby")
        self.assertEqual(response.json()["friend"]["display_name"], "Bobby")
        self.assertEqual(response.json()["friend"]["tags"], ["work", "friend"])

        with self.client.websocket_connect(f"/ws?token={alice}") as alice_ws:
            with self.client.websocket_connect(f"/ws?token={bob}") as bob_ws:
                alice_ws.send_json(
                    {
                        "type": "send_message",
                        "receiver": "bob001",
                        "message_type": "text",
                        "body": "Hello Bob",
                    }
                )
                self.assertEqual(alice_ws.receive_json()["message"]["message"], "Hello Bob")
                self.assertEqual(bob_ws.receive_json()["message"]["message"], "Hello Bob")

        response = self.client.get("/api/conversations/bob001/messages", headers=self.auth(alice))
        self.assertEqual(response.json()["messages"][0]["message"], "Hello Bob")

        response = self.client.delete("/api/friends/bob001", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get("/api/conversations", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        direct = next(item for item in response.json()["conversations"] if item["peer"]["number"] == "bob001")
        self.assertEqual(direct["status"], "inactive")
        self.assertEqual(direct["last_message"]["message"], "Hello Bob")

        response = self.client.get("/api/conversations/bob001/messages", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["messages"][0]["message"], "Hello Bob")

        response = self.client.post(
            "/api/conversations/bob001/messages",
            headers=self.auth(alice),
            json={"message_type": "text", "body": "Should not send"},
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_reciprocal_friend_request_accepts_existing_request(self):
        self.register("alice1", "Alice")
        self.register("bob001", "Bob")
        alice = self.login("alice1")
        bob = self.login("bob001")

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(bob),
            json={"receiver": "alice1"},
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(alice),
            json={"receiver": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "accepted")

        response = self.client.get("/api/friends", headers=self.auth(alice))
        self.assertEqual(response.json()["friends"][0]["number"], "bob001")

    def test_attachment_message_flow(self):
        self.register("alice1", "Alice")
        self.register("bob001", "Bob")
        alice = self.login("alice1")
        bob = self.login("bob001")

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(alice),
            json={"receiver": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post("/api/friends/requests/alice1/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/conversations/bob001/attachments",
            headers=self.auth(alice),
            files={"file": ("note.txt", b"hello file", "text/plain")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        message = response.json()["message"]
        self.assertEqual(message["type"], "file")
        self.assertEqual(message["attachment"]["name"], "note.txt")
        self.assertEqual(message["attachment"]["size"], 10)

        stored_name = message["attachment"]["url"].rsplit("/", 1)[-1]
        self.assertTrue((app_main.settings.upload_dir / stored_name).exists())

        response = self.client.get("/api/conversations/bob001/messages", headers=self.auth(alice))
        self.assertEqual(response.json()["messages"][0]["attachment"]["name"], "note.txt")

        response = self.client.get(message["attachment"]["url"])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.content, b"hello file")

        response = self.client.get(f'{message["attachment"]["url"]}?download=1')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("note.txt", response.headers["content-disposition"])

    def test_moments_feed_likes_and_comments(self):
        self.register("alice1", "Alice")
        self.register("bob001", "Bob")
        self.register("carol1", "Carol")
        alice = self.login("alice1")
        bob = self.login("bob001")
        carol = self.login("carol1")

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(alice),
            json={"receiver": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post("/api/friends/requests/alice1/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/moments",
            headers=self.auth(alice),
            data={"body": "first moment"},
            files=[("files", ("photo.png", b"fake image", "image/png"))],
        )
        self.assertEqual(response.status_code, 200, response.text)
        moment = response.json()["moment"]
        self.assertEqual(moment["body"], "first moment")
        self.assertEqual(moment["images"][0]["name"], "photo.png")

        response = self.client.get("/api/moments", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["moments"][0]["id"], moment["id"])

        response = self.client.get("/api/moments", headers=self.auth(carol))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["moments"], [])

        response = self.client.post(f"/api/moments/{moment['id']}/like", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["moment"]["liked_by_me"])
        self.assertEqual(response.json()["moment"]["likes"][0]["number"], "bob001")

        response = self.client.post(
            f"/api/moments/{moment['id']}/comments",
            headers=self.auth(bob),
            json={"body": "nice"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["moment"]["comments"][0]["body"], "nice")

        response = self.client.post(f"/api/moments/{moment['id']}/like", headers=self.auth(carol))
        self.assertEqual(response.status_code, 403, response.text)

        response = self.client.get(moment["images"][0]["url"])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.content, b"fake image")

        response = self.client.delete(f"/api/moments/{moment['id']}", headers=self.auth(bob))
        self.assertEqual(response.status_code, 403, response.text)

        response = self.client.delete(f"/api/moments/{moment['id']}", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "deleted")

        response = self.client.get("/api/moments", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["moments"], [])

        response = self.client.get(moment["images"][0]["url"])
        self.assertEqual(response.status_code, 404, response.text)

    def test_account_settings_flow(self):
        self.register("alice1", "Alice")
        alice = self.login("alice1")

        response = self.client.patch(
            "/api/me",
            headers=self.auth(alice),
            json={"nickname": "Alice Prime"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user"]["nickname"], "Alice Prime")
        self.assertIn("avatar_color", response.json()["user"])

        response = self.client.patch(
            "/api/me",
            headers=self.auth(alice),
            json={"current_password": "wrong-pass", "new_password": "newsecret1"},
        )
        self.assertEqual(response.status_code, 403, response.text)

        response = self.client.patch(
            "/api/me",
            headers=self.auth(alice),
            json={"current_password": "secret1", "new_password": "newsecret1"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post(
            "/api/auth/login",
            json={"number": "alice1", "password": "newsecret1"},
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/me/avatar",
            headers=self.auth(alice),
            files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar", "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        avatar_url = response.json()["user"]["avatar_url"]
        self.assertTrue(avatar_url.startswith("/api/avatars/"))

        response = self.client.get(avatar_url)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_group_invite_message_and_conversation_flow(self):
        self.register("alice1", "Alice")
        self.register("bob001", "Bob")
        self.register("carol1", "Carol")
        alice = self.login("alice1")
        bob = self.login("bob001")
        carol = self.login("carol1")

        response = self.client.post(
            "/api/friends/requests",
            headers=self.auth(alice),
            json={"receiver": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post("/api/friends/requests/alice1/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/groups",
            headers=self.auth(alice),
            json={"title": "Project Room", "members": ["bob001"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        group = response.json()["conversation"]
        invite = response.json()["invites"][0]
        self.assertEqual(group["type"], "group")
        self.assertEqual(group["owner"], "alice1")
        self.assertEqual(invite["invitee"], "bob001")
        self.assertEqual(response.json()["messages"][0]["type"], "group_invite")

        response = self.client.post(
            f"/api/conversations/{group['id']}/invites",
            headers=self.auth(alice),
            json={"invitees": ["bob001"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        duplicate_invite = response.json()["invites"][0]
        self.assertNotEqual(duplicate_invite["id"], invite["id"])

        response = self.client.get("/api/groups/invites", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual({item["conversation_id"] for item in response.json()["invites"]}, {group["id"]})

        response = self.client.get("/api/conversations/alice1/messages", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["messages"][0]["type"], "group_invite")

        response = self.client.post(f"/api/groups/invites/{invite['id']}/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["invite"]["status"], "accepted")

        response = self.client.get("/api/groups/invites", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["invites"], [])

        response = self.client.post(f"/api/groups/invites/{duplicate_invite['id']}/accept", headers=self.auth(bob))
        self.assertEqual(response.status_code, 409, response.text)

        response = self.client.get("/api/conversations", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        bob_group = next(item for item in response.json()["conversations"] if item["id"] == group["id"])
        self.assertEqual({member["number"] for member in bob_group["members"]}, {"alice1", "bob001"})

        response = self.client.post(
            f"/api/conversations/by-id/{group['id']}/messages",
            headers=self.auth(bob),
            json={"message_type": "text", "body": "Hello group"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["message"]["conversation_id"], group["id"])
        self.assertEqual(response.json()["message"]["message"], "Hello group")

        response = self.client.post(
            f"/api/conversations/by-id/{group['id']}/attachments",
            headers=self.auth(alice),
            files={"file": ("plan.txt", b"group file", "text/plain")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["message"]["attachment"]["name"], "plan.txt")

        response = self.client.get(f"/api/conversations/by-id/{group['id']}/messages", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            [message["message"] for message in response.json()["messages"]],
            ["Bob joined the group", "Hello group", "plan.txt"],
        )

        response = self.client.post(
            f"/api/conversations/{group['id']}/invites",
            headers=self.auth(alice),
            json={"invitees": ["carol1"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        carol_invite = response.json()["invites"][0]
        response = self.client.post(f"/api/groups/invites/{carol_invite['id']}/accept", headers=self.auth(carol))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.patch(
            f"/api/conversations/{group['id']}",
            headers=self.auth(alice),
            json={"title": "Renamed Room"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conversation"]["title"], "Renamed Room")
        self.assertEqual(response.json()["message"]["type"], "system")

        response = self.client.patch(
            f"/api/conversations/{group['id']}/me",
            headers=self.auth(bob),
            json={"alias": "B in Room"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conversation"]["my_alias"], "B in Room")

        response = self.client.patch(
            f"/api/conversations/{group['id']}/owner",
            headers=self.auth(alice),
            json={"owner": "bob001"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conversation"]["owner"], "bob001")
        self.assertEqual(response.json()["conversation"]["members"][0]["number"], "bob001")
        self.assertEqual(response.json()["message"]["type"], "system")

        response = self.client.patch(
            f"/api/conversations/{group['id']}/owner",
            headers=self.auth(bob),
            json={"owner": "alice1"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conversation"]["owner"], "alice1")

        response = self.client.delete(f"/api/conversations/{group['id']}/members/carol1", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("carol1", {member["number"] for member in response.json()["conversation"]["members"]})
        self.assertEqual(response.json()["message"]["type"], "system")

        response = self.client.delete(f"/api/conversations/{group['id']}/me", headers=self.auth(alice))
        self.assertEqual(response.status_code, 400, response.text)

        response = self.client.delete(f"/api/conversations/{group['id']}/me", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "left")

        response = self.client.get("/api/conversations", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        bob_group = next(item for item in response.json()["conversations"] if item["id"] == group["id"])
        self.assertEqual(bob_group["my_status"], "left")

        response = self.client.get(f"/api/conversations/by-id/{group['id']}/messages", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            f"/api/conversations/by-id/{group['id']}/messages",
            headers=self.auth(bob),
            json={"message_type": "text", "body": "Should not send"},
        )
        self.assertEqual(response.status_code, 403, response.text)

        with self.client.websocket_connect(f"/ws?token={bob}") as bob_ws:
            bob_ws.send_json(
                {
                    "type": "send_message",
                    "conversation_id": group["id"],
                    "message_type": "text",
                    "body": "Dropped group message",
                }
            )
            self.assertEqual(bob_ws.receive_json()["type"], "error")
            bob_ws.send_json(
                {
                    "type": "send_message",
                    "receiver": "alice1",
                    "message_type": "text",
                    "body": "Socket still works",
                }
            )
            self.assertEqual(bob_ws.receive_json()["message"]["message"], "Socket still works")

        response = self.client.delete(f"/api/conversations/{group['id']}", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "dissolved")
        self.assertEqual(response.json()["message"]["type"], "system")

        response = self.client.get(f"/api/conversations/by-id/{group['id']}/messages", headers=self.auth(bob))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("Group chat was disbanded", [message["message"] for message in response.json()["messages"]])

        response = self.client.get("/api/conversations", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)
        alice_group = next(item for item in response.json()["conversations"] if item["id"] == group["id"])
        self.assertEqual(alice_group["status"], "dissolved")

        response = self.client.get(f"/api/conversations/by-id/{group['id']}/messages", headers=self.auth(alice))
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            f"/api/conversations/by-id/{group['id']}/messages",
            headers=self.auth(alice),
            json={"message_type": "text", "body": "Should not send"},
        )
        self.assertEqual(response.status_code, 403, response.text)


if __name__ == "__main__":
    unittest.main()
