from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, number: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[number].add(websocket)

    def disconnect(self, number: str, websocket: WebSocket):
        sockets = self.connections.get(number)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self.connections.pop(number, None)

    async def send_to_user(self, number: str, payload: dict):
        dead = []
        for websocket in list(self.connections.get(number, set())):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(number, websocket)

    async def broadcast_message(self, message: dict, recipients: list[str] | None = None):
        payload = {"type": "message", "message": message}
        if recipients is not None:
            for number in recipients:
                await self.send_to_user(number, payload)
            return
        await self.send_to_user(message["sender"], payload)
        if message["receiver"] != message["sender"]:
            await self.send_to_user(message["receiver"], payload)


manager = WebSocketManager()
