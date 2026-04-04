import threading
import math
import random
import re
import string
import time
from email.mime.text import MIMEText

import database
import email_service


class ClientHandler:
    def __init__(self, client, ip_address, server_ref):
        self.client = client
        self.ip_address = ip_address
        self.server = server_ref
        self.number = None
        self.login_code = None
        self.register_code = None
        self.login_code_send_time = 0
        self.register_code_send_time = 0
        threading.Thread(target=self.listen, daemon=True).start()

    # ------------------------------------------------------------------ core
    def _recv_all(self):
        """先读4字节长度头，再读完整数据"""
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

    def _send_all(self, data: str):
        """先发4字节长度头，再发数据"""
        encoded = data.encode("utf-8")
        header = len(encoded).to_bytes(4, "big")
        self.client.sendall(header + encoded)

    def listen(self):
        while True:
            try:
                raw = self._recv_all()
                request = eval(raw)
                print(f"[{self.ip_address}] -> {request[0]}")
                try:
                    response = eval(f"self.{request[0]}")(request[1:])
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    response = (False, str(ex))
                self._send_all(repr(response))
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

    def count(self, table):
        return self.db_query(f"SELECT COUNT(*) FROM {table};")[0][0]

    def create_code(self, length):
        pool = string.ascii_letters + string.digits * 6
        return "".join(random.sample(pool, length))

    def validate_email(self, email):
        return bool(re.compile(r"^.+@.+").match(email))

    # ------------------------------------------------------------------ handlers
    def connect(self, info):
        self.hostname, self.mac_address = info

    def login(self, info):
        number, password = info
        if not number:
            return (False, "The number can't be empty")
        if not password:
            return (False, "The password can't be empty")
        sql = "SELECT number FROM users WHERE number = ? AND password = ?;"
        result = self.db_query(sql, number, password)
        if not result:
            return (False, "The number or password is wrong")
        if any(c.number == number for c in self.server.clients.values() if c is not self):
            return (False, "Account login elsewhere")
        self.number = number
        return (True, "succeeded")

    def getUserInfo(self, info):
        number = info[0]
        sql = "SELECT avatar, background, nickname, birth, gender, motto FROM users WHERE number = ?;"
        result = self.db_query(sql, number)
        if not result:
            return (False, "Account is not registered")
        return (True, tuple(result[0]))

    def modifyUserInfo(self, info):
        number, field, value = info
        # 允许刚注册的用户（self.number 尚未设置）更新自己的信息
        if self.number is not None and number != self.number:
            return
        sql = f"UPDATE users SET {field} = ? WHERE number = ?;"
        self.db_query(sql, value, number)

    def getLoginDevices(self, info):
        number = info[0]
        if number != self.number:
            return
        sql = "SELECT devices FROM users WHERE number = ?;"
        return (True, self.db_query(sql, number)[0][0])

    def register(self, info):
        number, password, email, code, mac_address = info
        if len(number) < 6:
            return (False, "The number length is at least 6")
        if len(password) < 6:
            return (False, "The password length is at least 6")
        if not email:
            return (False, "The email can't be empty")
        if code is None or code != self.register_code:
            return (False, "The verification code is wrong")
        if time.time() - self.register_code_send_time > 600:
            return (False, "The verification code has expired")

        if self.db_query("SELECT number FROM users WHERE number = ?;", number):
            return (False, "The number has already been registered")
        if self.db_query("SELECT number FROM users WHERE email = ?;", email):
            return (False, "The email has already been bound")

        uid = self.count("users")
        devices = {mac_address: self.hostname}
        sql = "INSERT INTO users(id, number, password, email, devices) VALUES (?, ?, ?, ?, ?);"
        self.db_query(sql, uid, number, password, email, str(devices))
        return (True, "Registered successfully")

    def sendRegisterCode(self, info):
        email = info[0]
        spacing = 60 - time.time() + self.register_code_send_time
        if spacing > 0:
            return (False, f"You need to wait {math.ceil(spacing)}s")
        if not email:
            return (False, "The email can't be empty")
        if not self.validate_email(email):
            return (False, "The email format is incorrect")

        self.register_code_send_time = time.time()
        self.register_code = self.create_code(6)
        html = open("SMTP HTML/Register Code.html", "rb").read().decode("utf-8") % self.register_code
        content = MIMEText(html, "html", "utf-8")

        # 在子线程发送邮件，异常会打印到终端但不阻塞响应
        def send_async():
            try:
                email_service.send_email(email, content, "Register Code")
                print(f"[email] Register code sent to {email}")
            except Exception as ex:
                print(f"[email] Failed to send to {email}: {ex}")

        threading.Thread(target=send_async, daemon=True).start()
        return (True, "Sent successfully")

    def uploadFile(self, info):
        fid = self.count("files")
        size, name, extension, data = info
        sql = "INSERT INTO files (id, size, name, extension, data) VALUES (?, ?, ?, ?, ?);"
        self.db_query(sql, fid, size, name, extension, data)
        return (True, fid)

    def downloadFile(self, info):
        fid = info[0]
        sql = "SELECT data FROM files WHERE id = ?;"
        result = self.db_query(sql, fid)
        if not result:
            return (False, "File not found")
        return (True, result[0][0])
