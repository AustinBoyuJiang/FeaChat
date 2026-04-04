import socket
import threading

import database
from client_handler import ClientHandler
from config import SOCKET_PORT, CLIENT_MAXIMUM


class SocketServer:
    def __init__(self):
        self.db = database.get_connection()
        self.clients: dict = {}
        self.ip_address = socket.gethostname()
        self.port = SOCKET_PORT
        self._running = False

    def build(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)  # 每秒超时一次，让主线程能响应 Ctrl+C
        self.socket.bind((self.ip_address, self.port))
        self.socket.listen(CLIENT_MAXIMUM)

    def listen(self):
        self._running = True
        print(f"Server listening on {self.ip_address}:{self.port}")
        try:
            while self._running:
                try:
                    client, ip_address = self.socket.accept()
                except socket.timeout:
                    continue  # 超时后回到循环顶部，检查 _running 标志
                print(f"[{ip_address}] connected")
                handler = ClientHandler(client, ip_address, self)
                self.clients[ip_address] = handler
        except KeyboardInterrupt:
            pass
        finally:
            self.close()
            print("Server stopped.")

    def close(self):
        self._running = False
        self.socket.close()
        self.db.close()
