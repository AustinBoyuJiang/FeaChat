# _*_coding:utf-8_*_

import _thread
import base64
import ctypes
import os
import socket
import sys
import uuid

from PIL import Image, ImageDraw, ImageFilter
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

DEV_MODE = False

DEV_MOCK_USERS = {
    "alice": ["Alice",    "dev_avatar", "dev_bg", "1995-03-12", "Girl", "Hello, I'm Alice!"],
    "bob":   ["Bob",      "dev_avatar", "dev_bg", "1992-07-08", "Boy",  "Hey there, Bob here."],
    "carol": ["Carol",    "dev_avatar", "dev_bg", "1998-11-25", "Girl", "Carol's motto."],
}

DEV_MOCK_MESSAGES = [
    ("0", "bob",   "alice", "2024-01-10 09:00:00", "text", "Hey Alice!"),
    ("1", "alice", "bob",   "2024-01-10 09:01:00", "text", "Hi Bob, how are you?"),
    ("2", "bob",   "alice", "2024-01-10 09:02:00", "text", "Doing great, thanks!"),
    ("3", "carol", "alice", "2024-01-10 10:00:00", "text", "Alice, are you free later?"),
    ("4", "alice", "carol", "2024-01-10 10:01:00", "text", "Sure, what's up?"),
]


def _setup_dev_assets():
    import shutil
    os.makedirs("data/temp", exist_ok=True)
    for src, dst in [
        ("pic/logo/avatar.png", "data/temp/dev_avatar"),
        ("pic/logo/logo.png",   "data/temp/dev_bg"),
    ]:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy(src, dst)


def get_user_info(number):
    if DEV_MODE:
        return feachat.user_info.get(
            number, ["Unknown", "dev_avatar", "dev_bg", "2000-01-01", "Boy", ""]
        )
    return feachat.getUserInfo(number)


def download_file(file_id, file_type):
    if DEV_MODE:
        return
    # 文件已缓存则跳过
    path = "data/temp/%s" % file_id
    if os.path.exists(path):
        return
    feachat.downloadFile(file_id)


class feachatUi:
    def __init__(self):
        self.name = "FeaChat"
        self.app = self.uiSetting()
        self.hostname = socket.gethostname()
        self.ipAddress = socket.gethostbyname(self.hostname)
        self.macAddress = self.getMacAddress()
        self.userInfo = self.readLocalData("user info")
        self.user_info = self.userInfo  # chat_ui 使用 user_info
        self.account = None
        self.connect = False

    def connectServer(self, host, port):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((host, port))
            self.connect = True
        except Exception as ex:
            print(ex)
            pass

    def request(self, *request):
        if not self.connect:
            return (False, "Server not connected")
        # 发送：4字节长度头 + 数据
        encoded = repr(request).encode("utf-8")
        self.server.sendall(len(encoded).to_bytes(4, "big") + encoded)
        # 接收：先读4字节长度头，再读完整数据
        header = b""
        while len(header) < 4:
            header += self.server.recv(4 - len(header))
        length = int.from_bytes(header, "big")
        data = b""
        while len(data) < length:
            data += self.server.recv(min(65536, length - len(data)))
        return eval(data.decode("utf-8"))

    def uiSetting(self):
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.name)
        app = QApplication(sys.argv)
        app.setEffectEnabled(Qt.UI_AnimateCombo, False)
        return app

    def getMacAddress(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[i : i + 2] for i in range(0, 11, 2)])

    def getStyleSheet(self, file):
        return open(f"style/{file}.qss").read()

    def cropCircle(self, img, width):
        square = img.resize((width, width))
        mask = Image.new("L", (width, width), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, width), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        result = square.copy()
        result.putalpha(mask)
        return result

    # 各本地数据文件的默认值
    _LOCAL_DEFAULTS = {
        "user info": {},
        "login history": {},
        "remember password": False,
        "messages": {},
    }

    def readLocalData(self, name):
        path = "data/local/%s.fct" % name
        if not os.path.exists(path):
            os.makedirs("data/local", exist_ok=True)
            default = self._LOCAL_DEFAULTS.get(name, {})
            self.writeLocalData(name, default)
            return default
        file = open(path, "r")
        data = eval(file.read())
        file.close()
        return data

    def writeLocalData(self, name, data):
        file = open("data/local/%s.fct" % name, "w")
        file.write(repr(data))
        file.close()

    def getUserInfo(self, number):
        if number not in self.userInfo:
            result = self.updateUserInfo(number)
            if result and result[0] == False:
                return
        return self.userInfo[number]

    def updateUserInfo(self, number):
        request = self.request("getUserInfo", number)
        if request[0] == False:
            return request[1]
        self.userInfo[number] = request[1]
        self.writeLocalData("user info", self.userInfo)

    def modifyUserInfo(self, number, type, value):
        self.request("modifyUserInfo", number, type, value)

    def getTempFile(self, id):
        return

    def uploadFile(self, path):
        request = self.request("uploadFile", *self.readFile(path))
        return request[1]  # (True, file_id)

    def downloadFile(self, id):
        os.makedirs("data/temp", exist_ok=True)
        path = "data/temp/%s" % id
        if os.path.exists(path):
            return
        result = self.request("downloadFile", id)
        if result and result[0]:
            import base64
            data = base64.b64decode(result[1])
            with open(path, "wb") as f:
                f.write(data)

    def readFile(self, path):
        size = os.path.getsize(path)
        file = os.path.basename(path)
        name = os.path.splitext(file)[0]
        extension = os.path.splitext(file)[-1]
        file = open(path, "rb")
        data = base64.b64encode(file.read()).decode("utf-8")
        file.close()
        return (size, name, extension, data)


feachat = None
