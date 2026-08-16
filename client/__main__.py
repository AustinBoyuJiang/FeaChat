import os
import sys


BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import core
from core import DEV_MODE, feachatUi
from ui.chat_ui import chatUi
from ui.login_ui import loginUi
from ui.shadow import uiShadow


core.feachat = feachatUi()

if not DEV_MODE:
    core.feachat.connectServer(core.SERVER_HOST, core.SERVER_PORT)
    core.feachat.request("connect", core.feachat.hostname, core.feachat.macAddress)

auto_number = os.getenv("FEACHAT_AUTO_LOGIN_NUMBER")
auto_password = os.getenv("FEACHAT_AUTO_LOGIN_PASSWORD")

if auto_number and auto_password:
    result = core.feachat.request("login", auto_number, auto_password)
    if not result[0]:
        print(f"Auto login failed for {auto_number}: {result[1]}")
        core.feachat.loginWindow = uiShadow(loginUi)
    else:
        core.feachat.number = auto_number
        core.feachat.account = auto_number
        core.feachat.password = auto_password
        core.feachat.user_info = {}
        core.feachat.userInfo = core.feachat.user_info
        core.feachat.user_info[auto_number] = core.feachat.getUserInfo(auto_number)
        core.feachat.chatWindow = uiShadow(chatUi)
else:
    core.feachat.loginWindow = uiShadow(loginUi)
