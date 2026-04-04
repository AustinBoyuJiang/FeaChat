# _*_coding:utf-8_*_

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core


def _make_simple_dialog(title_str, width=800, height=600):
    # Factory: generate simple dialog classes with identical structure.
    class _Dialog(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = title_str
            self.width = width
            self.height = height
            self.titleWidth = width
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;border-radius: 10px;")
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #727272;background-color: transparent;")
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30); self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×"); self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close"); self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;font-size: 25px;color: #727272;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#closeButton:hover{background-color: #e1e1e1;}QPushButton#closeButton:pressed{background-color: #c9c9c9;}")
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30); self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-"); self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize"); self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;font-size: 30px;color: #727272;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#minButton:hover{background-color: #e1e1e1}QPushButton#minButton:pressed{background-color: #c9c9c9;}")
    _Dialog.__name__ = title_str.replace(" ", "") + "Ui"
    return _Dialog


addFriendsUi = _make_simple_dialog("Add Friends")
createGroupUi = _make_simple_dialog("Create Group")
shareMomentsUi = _make_simple_dialog("Share Moments")
settingUi = _make_simple_dialog("Setting")
fileManagerUi = _make_simple_dialog("File Manager")


class messageBoxUi(QWidget):
    width = 500
    height = 300
    titleWidth = 500
    titleHeight = 40

    def __init__(self, window, parent, title, message, event):
        super().__init__(window)
        self.window = window
        self.parent = parent
        self.resize(self.width, self.height)
        self.parent.setWindowTitle(title)
        self.window.setWindowModality(Qt.ApplicationModal)
        self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
        self.setStyleSheet(core.feachat.getStyleSheet("messageBoxUi"))
        self.content = QLabel(self); self.content.resize(self.width, self.height); self.content.move(0, 0)
        self.content.setStyleSheet("background-color: #ffffff;border-radius: 10px;")
        self.titleText = QLabel(self); self.titleText.setGeometry(15, 0, 485, 40)
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #727272;background-color: transparent;")
        self.messageText = QLabel(self); self.messageText.setGeometry(20, 40, 460, 200)
        self.messageText.setText(message); self.messageText.setWordWrap(True)
        self.messageText.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.messageText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #000000;background-color: transparent;")
        self.closeButton = QPushButton(self); self.closeButton.setGeometry(self.width - 45, 5, 40, 30)
        self.closeButton.setText("×"); self.closeButton.setObjectName("closeButton")
        self.closeButton.clicked.connect(self.window.close)
        self.confirmButton = QPushButton(self); self.confirmButton.setGeometry(250, 240, 100, 40)
        self.confirmButton.setText("Confirm"); self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.clicked.connect(event)
        self.cancelButton = QPushButton(self); self.cancelButton.setGeometry(370, 240, 100, 40)
        self.cancelButton.setText("Cancel"); self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.clicked.connect(self.window.close)
        self.show()
