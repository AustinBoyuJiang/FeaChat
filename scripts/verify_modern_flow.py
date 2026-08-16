import asyncio
import json
import sys
import urllib.request

import websockets


API = "http://127.0.0.1:8000"


def post(path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read())


def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API + path, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read())


async def verify():
    alice = post("/api/auth/login", {"number": "alice1", "password": "secret1"})["token"]
    bob = post("/api/auth/login", {"number": "bob001", "password": "secret1"})["token"]
    friends = get("/api/friends", alice)["friends"]
    assert friends and friends[0]["number"] == "bob001"

    async with websockets.connect(f"ws://127.0.0.1:8000/ws?token={alice}") as alice_ws:
        async with websockets.connect(f"ws://127.0.0.1:8000/ws?token={bob}") as bob_ws:
            await alice_ws.send(
                json.dumps(
                    {
                        "type": "send_message",
                        "receiver": "bob001",
                        "message_type": "text",
                        "body": "modern hello",
                    }
                )
            )
            alice_event = json.loads(await alice_ws.recv())
            bob_event = json.loads(await bob_ws.recv())
            assert alice_event["message"]["message"] == "modern hello"
            assert bob_event["message"]["message"] == "modern hello"

    history = get("/api/conversations/bob001/messages", alice)["messages"]
    assert history[-1]["message"] == "modern hello"
    print("Modern REST/WebSocket flow OK")


if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except Exception as exc:
        print(f"Modern flow failed: {exc}", file=sys.stderr)
        raise

