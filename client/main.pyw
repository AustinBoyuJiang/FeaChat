# _*_coding:utf-8_*_

import _thread
import core
from core import feachatUi, DEV_MODE

core.feachat = feachatUi()

from ui.shadow import uiShadow
from ui.login_ui import loginUi

if __name__ == "__main__":
    if not DEV_MODE:
        core.feachat.connectServer(core.feachat.ipAddress, 8888)
        core.feachat.request("connect", core.feachat.hostname, core.feachat.macAddress)

    core.feachat.loginWindow = uiShadow(loginUi)
